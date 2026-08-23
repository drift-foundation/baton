# Finding: build the durable v12 Worker Manager core

Work `W2929`, child of W1425. This M2 slice follows the disposable assignment
authority W2928.

## Confirmed boundary

Implement the trusted host-side Worker Manager core against the landed v12
authority and the frozen `urn:baton:worker-control:1.0` and
`urn:baton:agent-session:1.0` contracts. The manager owns durable offer and
runtime-attempt control state, never authoritative Work/generation/gate state.

This slice is runtime-neutral. It defines the adapter interface but does not
perform Docker/Podman mutations, build a worker image, certify a provider, or
implement M3 proposal integration.

## Recommended patch ownership

Own v12-only worker-control codec/schema validation, shared control store,
manager orchestration, offer verifier, agent-session normalization, runtime
adapter interface, and their tests. Existing `0-spike` manager/token/envelope/
ACP modules are behavioral evidence and may be replaced or superseded; their
draft version and process-memory state must not leak into 1.0.

## Acceptance

- Validate exact 1.0 negotiation, canonical JSON/digests, limits, identities,
  manifests, artifact references and closed error pairs before use.
- Persist at most one nonterminal offer per Work, only token verifiers/digests,
  accepted intent and the fixed claim operation; bearer material is never
  durable.
- Separate token expiry from claim-settlement deadline and reconcile the fixed
  authority operation across manager restart without guessing from current
  Handler alone.
- Persist orthogonal consent/execution runtime, output, disposition, proposal,
  verification and cleanup observations without overloading Work phase.
- Enforce fresh consent/execution sessions, exact posture, supervised turns,
  bounded normalized events, unexpected-approval denial, cancellation order,
  and the distinction between agent and runtime quiescence.
- Cover exact retry/collision, duplicate/regressing observation, restart at
  every durable boundary, stale generation, output freeze/intake and cleanup
  blocked on intake. Keep all 68 M1 worker-control and agent-session design
  tests green (12 + 56) and add real implementation tests.

The implementer creates and exclusively owns `PROGRESS.md` when this Work is
routed for implementation.

## Reviewer revalidation — 2026-08-22

### Confirmed landed prerequisite

W2928 is closed satisfying and its latest independent review signs off the
disposable authority. The implementation is under `v12/src/authority/`; the
full v12 gate passes 159/159 and W151's executable model passes 54/54.

The manager consumes only the public `v12/src/authority/index.mjs` boundary.
The deployment hands it one participant-bound `V12Session`; it does not hand
it `V12Authority`, the authority store path, a store/database/SQL handle, or a
way to mint another participant's session. The session supplies the required
runtime reads and transitions, including `projectWork`, `slotHolder`,
`operationRecord`, `claim`, `settleOperation`, `activity`, `cancel`, `end`,
`pass`, `publish` and typed-gate operations. The pure static
`V12Authority.claimSignature(workId, participant)` is the fixed authority
claim signature and grants no bootstrap capability.

**Confirmed distinction:** that authority claim signature is a canonical
internal operand string. It is not worker-control's SHA-256
`signature_digest`. The manager must persist and compare both at their
respective boundaries rather than reuse one as the other.

W2928 fixes the Node floor at 22.5 and uses built-in `node:sqlite`. Reusing
that mechanism for a separate manager database is compatible with the landed
package and avoids coupling the two stores. Sharing a database file, schema or
transaction with the authority is forbidden by W151's ownership split.

### Observed current implementation delta

The current `v12/src/manager.mjs`, `claim_token.mjs`, `envelopes.mjs` and
`acp_session.mjs` remain the accepted `0-spike`:

- `Manager` constructs a v11 CLI client and issues Docker-specific mutations
  through `container.mjs`; it does not consume `V12Session`.
- `ClaimTokenIssuer` keeps its signing secret and issued/spent map only in
  process memory.
- `envelopes.mjs` accepts `version: "0-spike"`, authority-local Work selectors,
  shallow shapes and unknown fields.
- `ContainerAcpSession` is Claude/ACP/container-specific, uses one ad-hoc event
  callback, and does not mint or persist the four sealed agent-session 1.0
  documents.
- No JavaScript implementation consumes either frozen 1.0 JSON Schema; the
  package has no JSON Schema or RFC 8785 implementation dependency.

These modules remain behavioral evidence for deadlines, refusal, redaction,
containment and reap-before-release ordering. They are not an implementation
base whose draft identities or direct Docker calls may leak into the new
boundary. The new manager path must be separately importable and testable
without importing `baton_cli.mjs`, `container.mjs`, `runtime.mjs` or a provider
adapter.

### Confirmed frozen contract seams

The implementation must compose four independent version/identity axes:

1. authority contract `v12-assignment-1` and its full assignment identity;
2. `urn:baton:worker-control:1.0` envelopes and manifests;
3. `urn:baton:agent-session:1.0` profile/session/turn/event documents; and
4. any underlying agent wire or provider binding, which remains adapter
   private.

The worker endpoint and agent endpoint are different untrusted roles. The
ephemeral claim bearer crosses `offer.issue` to the worker endpoint, but
agent-session 1.0 explicitly forbids forwarding it into a consent prompt or
session record. The worker endpoint may combine a normalized consent decision
with the bearer it received; agent prose and provider session ids never gain
claim authority.

Every durable 1.0 object is sealed and copied at the boundary. JSON Schema is
necessary but insufficient: the manager must also enforce RFC 8785 canonical
bytes, SHA-256 digests, identity-prefix equality, path/URI/content-tree rules,
capability selection, operation signatures, observation monotonicity, receipt
chains, event seals and secret exclusion. A partial hand validator is not a
conforming substitute for the frozen schemas plus semantic checks.

The product copy of each schema should live under the self-contained `v12/`
subtree and have a byte-identity regression against the canonical dossier
asset. Reading `work/records/` at runtime would make the executable depend on
review evidence; silently maintaining a divergent copy would create a second
contract.

### Confirmed contract conflict filed as W4487

W151 section 7 says a decline validates an exact unspent token and consumes
its verifier. Worker-control 1.0 section 6.1 and its schema require
`claim_token: null` for `decision=decline`. Both cannot be implemented.

The conflict is bound to top-level W4487 at
`work/records/2026/08/finding-worker-control-decline-token-conflict/` because
this record is already at the maximum dossier nesting depth. An asynchronous
authority ruling is pending. W2929 must not guess, weaken schema validation or
ship either decline behavior until W4487 explicitly supersedes one contract
and regenerates the affected schema/vectors.

## Proposed implementation boundary

The following layout is proposed; exact filenames may change while the
ownership boundaries may not:

- `v12/src/worker_manager/contracts.mjs` plus product schema assets: exact
  version/capability negotiation, schema validation, sealed copies, RFC 8785
  canonicalization, digests, semantic validators and the closed error-pair
  mapping.
- `v12/src/worker_manager/store.mjs` and `schema.mjs`: the one shared durable
  manager control store, transaction/CAS helpers and manager-owned operation
  replay.
- `v12/src/worker_manager/offers.mjs`: offer issue/decision/expiry/restart and
  fixed authority-claim settlement against an injected `V12Session`.
- `v12/src/worker_manager/attempts.mjs`: assignment activation, orthogonal
  attempt observations, cancellation ordering, output freeze/intake and
  cleanup orchestration.
- `v12/src/worker_manager/agent_session.mjs`: provider-neutral profile
  certification, fresh-session/turn/event normalization and durable event
  observation.
- `v12/src/worker_manager/adapter.mjs`: narrow runtime and agent adapter
  interfaces plus result validation. It performs no Docker, Podman, process,
  mount or provider mutation itself; W2930 supplies the local OCI adapter and
  worker endpoint.
- `v12/src/worker_manager/index.mjs`: the only public manager-core surface.
  Constructors receive an already minted `V12Session`, control-store handle,
  exact profiles, adapters, clock and id source. They never receive the
  authority bootstrap or store path.

The existing spike modules may stay as explicit `0-spike` evidence until the
later composition replaces their entry point. New 1.0 code must not import or
return their envelope, token or assignment shapes.

## Proposed durable control-store model

One SQLite file beneath the already validated external `state_root` owns the
following manager facts. Configuration names its exact path; no ambient
default points into the checkout.

1. **Meta/profile tables:** schema version, manager instance/incarnation,
   frozen worker-control limits/capabilities, certified runtime and
   agent-session profiles with their exact digests.
2. **Offer:** `offer_id`, full Work/participant binding, issuing incarnation,
   runtime attempt, readiness episode as advisory evidence, input/policy/
   profile digests, token verifier digest and issue/expiry times. A partial
   unique index permits at most one `issued` or `accepted` offer per Work
   across all manager processes.
3. **Offer settlement:** immutable intent digest/time, independently stored
   claim-settlement deadline, deterministic claim operation id, fixed
   authority signature, terminal disposition/reason and exact assignment
   result. The offer states are exactly W151's issued, accepted, claimed,
   declined, expired, settlement-expired, claim-refused and
   abandoned-after-restart outcomes.
4. **Attempt:** one row per `runtime_attempt_id`, optional exact assignment,
   adapter/profile/input/policy/image/toolchain digests, opaque runtime id,
   manager observation sequence, and the ten orthogonal runtime/output/
   workflow/cleanup axes frozen by the runtime-attempt manifest.
5. **Manager operation journal:** operation id, full effective signature,
   state, byte-stable result or durable refusal. Start, cancel, freeze,
   collect, retain, intake and destroy each settle here independently of any
   authority operation. Replay may never regress a stronger observation.
6. **Runtime observations:** adapter incarnation/runtime/source sequence,
   immutable observation digest and manager observation sequence. Exact
   duplicates replay; conflicting duplicates or state regressions refuse.
7. **Output and intake:** immutable freeze/result/quarantine records, artifact
   references, exact digests, pending or terminal intake disposition, and
   cleanup result. Cleanup's `blocked-on-intake` refusal is durable to its own
   operation; a later re-evaluation uses a new operation.
8. **Agent session evidence:** certified profile bytes, one session record per
   `(attempt, posture, epoch)`, turn records, sealed normalized events, and a
   separate observation row carrying lateness, manager sequence and
   replay/drop status. Durable rows and returned values are copies, never
   caller-owned aliases.

Bearer values, credentials, host paths containing secrets, raw provider
approval payloads and authority configuration/store locators are absent from
every table. Persisted message bodies containing the claim token are likewise
forbidden; only verifier/body/signature digests and redacted diagnostics may
survive.

## Proposed orchestration and restart cuts

### Offer and claim

1. Re-read `session.projectWork(workId)`, verify open/queued/unclaimed/no gate,
   verify the exact local certified profile for its contract, and check
   `session.slotHolder(session.participant)` before spending entropy.
2. In one control-store transaction, allocate offer/attempt identities, store
   the verifier digest and pinned digests, and win the per-Work nonterminal
   offer CAS. Emit the raw token only after that commit.
3. Validate a returned control envelope and body digest before fields, compare
   exact offer/runtime/Work binding and verifier in constant time, then commit
   the issued-to-accepted CAS before bearer expiry. That transaction consumes
   the verifier, freezes the intent digest, derives one deterministic claim
   operation id, and stores a separate claim-settlement deadline.
4. Submit only that operation through the participant-bound session. A claim
   result is recorded before `assignment.activate`; no writable adapter method
   is callable while the claim is ambiguous.
5. On a lost result, call `settleOperation` with the fixed authority signature.
   Before the settlement deadline it may only observe (`mayRetire=false`). At
   or after the deadline it may retire as `settlement-expired`; positive
   evidence that the submitted claim refused permits immediate retirement as
   `claim-refused`. Every path adopts an existing retirement's bound
   disposition/reason, and a signature collision changes no control row.
6. If the authority commit wins but the manager dies before recording it,
   restart records that exact committed assignment late. If the authority is
   unavailable, the offer remains accepted and execution stays disabled.

An `issued` offer from a prior manager incarnation is not accepted after
restart. It remains visible until expiry or an explicit abandonment CAS, its
verifier is consumed, and a later offer uses a new bearer. An `accepted` offer
is recoverable because its authorization and fixed claim operation are
durable. Multiple active managers coordinate only through the shared store;
one process never abandons another live incarnation's offer merely because it
did not mint the bearer itself.

### Runtime, cancellation, output and cleanup

- `assignment.activate` fixes and validates the assignment manifest before
  the first writable adapter call.
- Runtime start commits `start-requested` under a stable manager operation,
  then reconciles by opaque runtime id plus full assignment/profile labels.
  Zero positively identified runtimes permits a retry only after prior absence
  is proven; one reattaches; mismatch or multiplicity cancels rather than
  starting another.
- Adapter observations advance only through the frozen axes. `unreachable` or
  agent-session `unknown` never becomes `destroyed`.
- Cancellation calls `session.cancel(expect=assignment, ...)` first, so the
  authority atomically fences and ends the generation and installs the typed
  quiescence gate. Only then does the manager order agent cancellation and
  runtime stop. Agent quiescence cannot satisfy that gate.
- Freeze requires the exact live assignment, terminal agent-turn handling
  compatible with the declared disposition, and a positive writer-quiescence
  observation. The same digest replays; changed bytes under the same identity
  refuse. W2930 owns filesystem/OCI collection, while W2929 owns the immutable
  store transition and validation of the adapter's sealed observation.
- Ended-assignment material is sealed/quarantined. Intake changes only its
  trusted disposition and never publishes on the dead generation. Destruction
  waits for the recorded intake/discard policy; cleanup never changes
  authority state.

### Agent session normalization

The core certifies one exact profile by composing shape, document seal and
policy checks in that order. It opens separate consent and execution sessions,
each with a fresh per-posture epoch; it never resumes, forks, promotes or
re-prompts after transport loss. Consent has no assignment/workspace/output,
execution has the exact assignment and pinned workspace role, and neither
receives Baton capability.

Every turn has a manager deadline. Turn outcome is selected only from the
closed eight-value vocabulary and only from a terminal provider fact, policy
failure, deadline or transport death. It gates but never chooses worker
disposition. Unexpected approvals use the provider adapter's certified
no-grant answer, mark `policy-failed`, and enter cancellation/quarantine.

Normalized events use the closed ten kinds, bounded/redacted content and one
sealed frame digest. The relay sequence is per session epoch. The store adds
observation sequence/lateness/replay status beside the frame. Exact duplicates
replay; a conflicting duplicate, cross-session identity, non-positive
sequence or regression refuses. Queue overflow is bounded and counted rather
than silently lost.

## Required implementation regressions

The implementation should add focused Node suites, using real SQLite files
and deterministic scripted adapters rather than process-memory doubles:

- schema byte identity, exact 1.0 negotiation, all canonical vectors,
  unknown-field refusal, body/manifest/event seals, closed error pairs and
  semantic validation negatives;
- one-offer-per-Work CAS across two manager processes while independent Works
  proceed; bearer absence from the database, logs, errors, manifests and
  events;
- expire/replay/forgery/cross-binding and post-restart offer behavior, plus the
  W4487-ruled decline behavior;
- claim commit before/after result loss, pre/post settlement deadline,
  authority lookup failure, submitted refusal, retirement/control-row crash,
  bound-disposition replay and operation collision;
- restart after offer issue, acceptance, authority claim, assignment record,
  start request, runtime identity, freeze request, frozen result, intake and
  cleanup; no restart boundary mints a second claim/runtime/result;
- duplicate and regressing runtime/session observations, start multiplicity,
  stale assignment after cancellation/release/pass/close and immediate
  same-participant successor generation;
- fresh consent/execution sessions, posture swap, unsupported negotiation,
  policy drift, unexpected approvals, deadlines, transport loss, late and
  conflicting events, bounded overflow and no agent-quiescence gate evidence;
- freeze exact replay/change refusal, intake idempotence, cleanup blocked on
  intake, later new-operation cleanup, and cancellation fence-before-stop.

The scripted runtime/agent interfaces must make every call and injected crash
observable so tests assert ordering, not only final state. At least the frozen
conformance cases `C-claim-ambiguous-no-execution`,
`C-claim-settled-by-operation`, `C-consent-then-execution`,
`E-exact-replay`, `E-manager-restart-reconciles`, `E-operation-collision`,
`H-axis-monotonic` and `H-fresh-session` should drive the real core now; W2931
later owns the complete black-box 106-case local-OCI assessment.

## Focused verification baseline

Evidence is retained in `evidence/baseline-2026-08-22.txt`.

- `cd v12 && npm test`: 159 passed, 0 failed.
- W151 executable model: 54 passed.
- Worker-control 1.0 executable model: 12 passed.
- Agent-session 1.0 executable model: 56 passed.

The first attempted Python form used `pytest`, which is not installed in the
system interpreter. The records specify `unittest`; the exact recorded forms
above pass. This is an invocation correction, not a missing dependency or
contract failure.

## Open implementation decisions

- **Blocking:** W4487 must rule and regenerate the decline contract before the
  decline path or final W2929 implementation handoff.
- **Non-blocking:** choose and pin a Draft 2020-12 validator and RFC 8785
  implementation, or provide equivalently exhaustive local implementations.
  The observable boundary is already frozen: no choice may relax schema,
  canonicalization or sealed-copy requirements.
- **Non-blocking:** exact module names and internal table normalization are the
  implementer's choice. The public/session/store/adapter ownership split and
  crash boundaries above are acceptance requirements, not layout advice.

## Implementation handoff revalidation — 2026-08-22T15:36:19Z

### Superseded blocker

The **Blocking** W4487 bullet immediately above is superseded. W4487 closed
satisfying after two correction rounds and a final independent review with no
findings. The ruled decline shape and both integrity boundaries are pinned in
plan items 1a and 1b. W2929 must implement those current rules; it must not
reopen the historical contradiction or implement either pre-W4487 shape.

### Current-tree facts

- W2928 remains closed satisfying. Its public
  `v12/src/authority/index.mjs` boundary still exports the participant-bound
  `V12Session`; the session supplies the reads and transitions this dossier
  names without exposing its store. `claim` derives the participant from that
  binding and refuses a caller-supplied participant operand.
- No `v12/src/worker_manager/` implementation exists, and current v12 source
  and tests do not name either frozen 1.0 contract URN. The old `0-spike`
  modules therefore remain evidence only, exactly as described above.
- The package still has no JSON Schema Draft 2020-12 or RFC 8785 dependency.
  Selecting and pinning conforming implementations remains an implementer
  choice; relaxing the frozen schema or semantic validators does not.
- The working tree contains other participants' uncommitted W2928, W2907 and
  unrelated Baton changes. W2929 owns new `v12/src/worker_manager/` modules,
  product schema copies, focused manager tests, and implementer-created
  `PROGRESS.md`. It does not own edits inside `v12/src/authority/`; any
  necessary shared-file edit such as `v12/package.json` must preserve the
  current diff.

### Revalidated gates

`evidence/revalidation-2026-08-22T15-36-19Z.txt` records the exact commands:
v12 **161/161**, W151 **64/64**, worker-control **24/24**, conformance
**74/74**, and agent-session **56/56**. The retained 159-test v12 baseline is
historical; W2907's fixture-ownership regressions account for the two new
tests, not any W2929 implementation.

W2929 is implementation-ready for `baton.impl`. The implementer creates and
exclusively owns `PROGRESS.md`, re-reads this whole record and the exact W151,
worker-control and agent-session specifications, and revalidates these facts
before changing code.

## Implementation revalidation — 2026-08-22 (baton.claude)

Every pinned decision was re-checked against the tree before it was used. The
handoff revalidation of 15:36:19Z still holds: `V12Session` is the public
boundary, no 1.0 manager implementation existed, and all five gates passed.
W4487 closed satisfying, so plan items 1a and 1b are settled contract facts
rather than open questions.

### The first slice, and what it deliberately is not

This turn landed the contract boundary and the durable control store — the
foundation plan item 2 names — and **did not start** plan items 3 and 4. The
Work returns for review of that foundation rather than being held across a
context boundary, with `next` set back to `baton.impl`. `PROGRESS.md` lists
exactly what is absent; the acceptance boundary is long enough that two green
suites could otherwise be read as more than they are.

### Decisions taken beyond the boundary

- **The closed error PAIRING is written out in product code.** The frozen
  schema carries `category` and `code` as flat enums and does not pair them —
  which is precisely why §12 makes the pairing a semantic rule. A regression
  asserts the union of the written pairs is exactly the schema's two enums, so
  a code added to the contract fails loudly instead of becoming unmappable.
  A reviewer may prefer the pairing move into the contract asset instead;
  that is a contract change and was not made unilaterally here.
- **The schema is a sealed byte copy with a byte-identity regression.** A
  paraphrase would be a second, quieter contract: the first time the two
  disagreed, only the running one would matter.
- **The manager's operation signature reuses the wire payload shape.** Kind
  plus durable operands, so a manager reading its own journal and a peer
  reading the frame are talking about one identity rather than two that
  happen to travel together.
- **The bearer-absence regression reads the FILE, not the code.** It reopens
  the database as a plain `DatabaseSync` and sweeps every column of every
  table, and asserts the verifier IS present so the absence is a real
  assertion rather than an empty table.
- **`v12-manager-` is registered in the W2907 owned-root family list**, so
  the fixture-cleanup regressions account for the new family rather than
  silently ignoring it.

### Open, and named rather than glossed

The non-blocking validator decision is still open, and this slice does not
close it: the semantic rules and the seals are validated by hand, and no
document is yet run through a Draft 2020-12 validator. So "unknown-field
refusal" from the acceptance list is **not covered**. Choosing the validator
is the first thing the next slice should do, because several acceptance items
depend on the choice.

## Independent first-slice review — 2026-08-22 (baton.codex)

**Confirmed:** this slice keeps authority state out of the manager database,
the product schema copy is byte-identical to the frozen asset, valid W4487
operation signatures use the ruled payload and verifier, and the partial
unique index enforces one nonterminal offer per Work across connections. The
closed error pairing may remain a semantic product mapping with its exhaustive
agreement regression; moving it into the already frozen schema is not needed.

**Supersession:** the implementation's paragraph immediately above calls
Draft 2020-12 validation a non-blocking open decision. The *library choice*
remains open, but validation itself is now blocking before further
orchestration. Without it, `validateEnvelope` exempts every non-`command`
string from operation-signature recomputation. A misspelled `commmand` carrying
a stale signature passes, so the open gap is not limited to unknown fields.

**Observed — changes requested:** the first-slice foundation also:

1. accepts a hello missing required limits/profile facts, selects every peer
   extension without local support, and returns no effective limits;
2. keys observations by attempt/source sequence even though source sequence is
   scoped to the stored adapter incarnation, so a restart's valid sequence 1
   collides with the earlier incarnation's sequence 1;
3. stores only durable refusal prose and replays every pair as
   `refused.precondition`; it also timestamps every operation at the Unix
   epoch instead of the manager clock;
4. executes version-1 schema DDL before refusing a version-99 store, changing
   a store it declares incompatible and leaking the throwing handle; and
5. canonicalizes negative integers, negative zero and lone surrogates even
   though the frozen canonical contract forbids them.

The exact correction boundaries are in
`review-2026-08-22T16-37-37Z.md`; deterministic reproductions are retained in
`evidence/review-foundation-edges.mjs`.

## Independent corrected-foundation re-review — 2026-08-22 (baton.codex)

**Confirmed corrected:** every finding in the first review now has a green
product regression: schema-first dispatch, exact complete negotiation,
incarnation-scoped observation identity, complete durable-refusal replay with
the manager clock, non-mutating incompatible-store refusal, and the reported
canonical value-space negatives.

**Observed — changes requested:** five adjacent foundation boundaries remain.
The exported operation-signature helper accepts a caller-supplied
`schemaProven: true` as proof and thereby reopens the reply exemption to an
unvalidated misspelled discriminator. The validated envelope is the same
mutable object supplied by the caller rather than the copied boundary this
dossier requires. The operation journal conflates “no row” with a committed
JSON `null`, so an exact retry executes again. Lone surrogates refuse in
string values but acquire digests in object member names. Negotiation validates
the peer and welcome but returns a malformed local runtime-profile digest as
trusted state.

The exact correction boundaries and severities are in
`review-2026-08-22T17-30-46Z.md`. Five additive regressions fail
deterministically; the command and locations are retained in
`evidence/review-corrected-foundation-edges-2026-08-22.txt`.

## Independent foundation round-three re-review — 2026-08-22 (baton.codex)

**Confirmed corrected:** the operation-signature proof is no longer public or
self-attested, validation owns its returned copy, committed JSON `null` has a
distinct presence result, malformed Unicode member names refuse, and local
negotiation policy is held to the frozen constraints. The focused baseline is
200/200 before new reviewer cases.

**Observed — changes requested:** three foundation boundaries remain. First,
the product still has no semantic trust entry for input manifests: the frozen
schema deliberately accepts a source URI containing a query and delegates its
refusal to section 12, while `contracts.mjs` names a nonexistent `validateUri`
and implements none of the manifest destination/URI/content-tree checks. The
frozen `durable-source-query-refused` vector therefore passes the only product
manifest validator available. Second, `ControlStore.transact` serializes an
action result directly into the operation journal without calling the landed
durable-secret walk, so a nested `claim_token` reaches the database. Third, a
pre-existing WAL database with application tables but no Baton `meta` table is
treated as fresh and silently receives all manager tables.

The exact correction boundaries and severities are in
`review-2026-08-22T18-14-12Z.md`. Two additive store regressions fail
deterministically; the semantic-manifest absence probe and full output are
retained in `evidence/review-foundation-round3-2026-08-22.txt`.

## Round-3 foundation correction — 2026-08-22

Three findings, all reproduced before any edit, all correct. Two decisions
worth pinning, plus one honest record.

**The §12 manifest trust entry is copied and schema-first, and its absence
was arguable from a comment.** The AJV setup justified disabling
`format: "uri"` assertions on the grounds that a `validateUri` "enforces
below" a stronger rule — and nothing had written that helper. The comment was
the only evidence the boundary existed. `validateManifest` now runs the
frozen schema fragment first and then the pure §12 rules on an independently
owned copy, and the §12 rules that need orchestration state — rule 2's live
assignment generation and rule 11's observation monotonicity — are named as
absent rather than approximated here.

Two shapes inside it are deliberate. Destinations are checked for OVERLAP,
not equality: a declared output inside a source directory has the worker
writing into delivered material, and the tree seal over that source stops
describing what is on disk. And rule 4 is read off the ORIGINAL URI text as
well as a parse, because the rule is about what a durable string may contain
and a parser's normalized reconstruction is not that string.

**Artifact references and content manifests are found by a walk.** The rule
is about what a durable document CONTAINS, at any depth — the same argument
as §13's secret walk. A check keyed on the field paths a current schema
revision happens to use would miss the human contract's locator, which is
exactly as durable as a source's; a regression witnesses that one
specifically.

**Recorded: one of my own regressions passed for the wrong reason.** The
frozen record expresses an invalid vector as a patch against a named valid
one, and my first version did not reseal `manifest_digest` — so both semantic
vectors were refused by the digest check and never reached the rules they
exist to witness. A mutation removing the whole input-manifest semantic block
left them green. They reseal now and assert the refusal the record names. A
vacuous vector test is worse than none, because it reads as agreement with
the frozen contract.

## Independent foundation round-four re-review — 2026-08-22 (baton.codex)

**Confirmed corrected:** the copied schema-first semantic manifest entry is
present, the journal now invokes its durable-secret guard on committed results
and sealed refusals, and only a genuinely empty database is initialized. The
full v12 baseline is 213/213 before new reviewer cases.

**Observed — changes requested:** three trust details remain. `validateUri`
swallows every `new URL` parse failure, so a resealed manifest trusts the
malformed hierarchical URI `https://[`. Content entry ordering uses
JavaScript's UTF-16 `<` rather than the contract's bytewise order and accepts
an astral-before-BMP counterexample that UTF-8 orders oppositely. Finally, the
durable-secret walk rejects only secret-looking member names: the raw claim
bearer commits under a benign `diagnostic` key and is also persisted inside a
durable refusal message.

The exact correction boundaries and severities are in
`review-2026-08-22T18-51-48Z.md`. Four additive regressions fail
deterministically; the probes and focused output are retained in
`evidence/review-foundation-round4-2026-08-22.txt`.

## Round-4 foundation correction — 2026-08-22

Three P1s, all in code I landed the round before: the manifest trust entry
closed a real hole and opened three smaller ones. Two decisions worth
pinning.

**A locator this build cannot parse is never trusted state.** `validateUri`
used to swallow parse failures on the theory that a failure meant an opaque
scheme. It does not — `https://[` is a malformed hierarchical URI — and since
this module argues for turning schema format assertions OFF, that swallow was
the only thing standing between a malformed locator and a trusted manifest.
Refusing costs the contract nothing, which was measured rather than assumed:
`artifact://`, `https://`, `file:///`, `urn:` and `mailto:` all parse, and
the opaque forms still answer to the original-text query and fragment rules.

**A leak boundary tests VALUES, not field names.** Screening member names
reads as §13 enforcement while being a naming convention — a bearer under
`diagnostic`, or interpolated into a durable refusal message, was journalled.
Shape cannot stand in for the value: the contract admits any bearer from 32
to 4096 characters, so refusing token-shaped strings would refuse ordinary
durable operands and still miss a short one.

So the manager holds the ephemeral secrets it knows, by VALUE, and refuses
any durable string that CONTAINS one. Containment rather than equality
because interpolation is the realistic leak. Registration is by value and not
by owner, because the question at a durable surface is only "is this the
secret", never "whose was it". `withSecret` releases in a `finally`, since a
caller that threw must not leave a value live and an unbounded set of dead
strings is scanned on every durable write.

`GOLDEN_BEARER` is seeded because it is the one bearer value this BUILD holds
as a constant, and a manager that wrote its own known secret to disk would be
leaking whatever the field was called. The VERIFIER is deliberately not
refused — it is the whole point of having one, and refusing it would make the
durable offer record impossible.

**Also pinned: content entries sort by UTF-8 bytes.** JavaScript `<` is
UTF-16 code-unit order and disagrees with the frozen model about astral
paths. This is a cross-language seal boundary, so the order the contract
names is the only one that may be accepted; the regression asserts the
fixture's two orderings disagree before asserting which one is refused, so it
cannot pass vacuously.

## Independent foundation round-five re-review — 2026-08-22 (baton.codex)

**Confirmed corrected:** parser-invalid locators refuse, content manifests
compare normalized paths by UTF-8 bytes, and the known golden bearer refuses
under benign result and refusal-message fields. The focused corrected
foundation baseline is 61/61.

**Observed — changes requested:** the journal walks the action result and
then serializes it separately. A `toJSON` method returns the golden bearer
only during serialization, so the guard passes and the operation row commits
the raw secret. Separately, the known-secret `Set` does not represent
overlapping lifetimes: an inner `withSecret` deletes an outer registration of
the same value, and its synchronous `finally` releases a Promise-returning act
before the asynchronous continuation settles.

The exact correction boundaries and severities are in
`review-2026-08-22T19-11-31Z.md`. Three additive regressions fail
deterministically; the focused output and managed full-gate limitation are
retained in `evidence/review-foundation-round5-2026-08-22.txt`.

## Round-5 foundation correction — 2026-08-22

Two P1s, both in the secret boundary landed the round before. Two decisions
worth pinning and one alternative declined.

**THE DURABLE BOUNDARY IS THE SERIALIZED REPRESENTATION.** Walking the
action's object and serializing it separately are two observable reads of a
value the manager did not construct, and a `toJSON` can answer them
differently. So the value is serialized ONCE, the parse of those exact bytes
is what gets walked — `JSON.parse` runs no user code, so the walk sees
precisely what will be stored — and the same bytes are recorded. Not
reserializing afterwards is part of the rule, not an optimization: a stateful
`toJSON` or getter would otherwise reopen the identical gap.

**PRESENCE IS NOT OWNERSHIP, AND A RETURN IS NOT COMPLETION.** The secret
registry became two registers because two lifetimes were being conflated. The
golden conformance bearer is PINNED — nothing acquired it, so nothing may
hand it back, and a scoped use of it must not delete the one value this build
knows at rest. Everything else is REFERENCE COUNTED, so an inner scope cannot
end an outer owner's lifetime and an unbalanced release is inert rather than
negative. `withSecret` transfers ownership to the continuation when its act
returns a thenable: a provider act's Promise is not its completion, and
releasing at Promise creation unregisters the bearer while the work is still
pending.

**DECLINED, and offered back.** The review's alternative — remove the scoped
API until its real orchestration caller can define the lifetime — was
considered. The API is what makes this boundary usable rather than a
convention every future caller must remember, and both of its failure modes
are now regressions. If the reviewer would still rather it wait for its
caller, deleting it is a small change.

## Independent foundation round-six re-review — 2026-08-22 (baton.codex)

**Confirmed corrected:** the journal screens and records one exact serialized
representation; reference-counted and pinned secret lifetimes survive nested
and Promise-returning scopes. The focused corrected baseline is 68/68.

**Observed — changes requested:** the successful first transaction still
returns the caller-owned pre-serialization object, while an exact retry
returns the parsed durable representation. A safe custom `toJSON` therefore
produces two different answers for one operation identity and violates the
pinned copy boundary. Separately, `withSecret` reads a thenable continuation
to classify it and `Promise.resolve` reads it again; a stateful thenable can
have the wrapper settle and release its bearer without ever running the
continuation observed on the first read.

The exact correction boundaries and severities are in
`review-2026-08-22T19-31-47Z.md`. Two additive regressions fail
deterministically; focused evidence is retained in
`evidence/review-foundation-round6-2026-08-22.txt`. The scoped API may stay:
capture and assimilate its continuation once rather than rediscovering it.

## Round-6 foundation correction — 2026-08-22

Two P1s, both the round-five corrections split one level down. One rule
covers them.

**A READ THAT DECIDES SOMETHING MUST BE THE READ THAT IS USED.** Round five
established that the durable boundary is the serialized representation and
then returned the caller's object beside the recorded bytes; and it captured
the decision "this act is asynchronous" from one read of `then` while letting
`Promise.resolve` act on another. Both are the same time-of-check /
time-of-use split, one at the journal and one at the scope.

So `_durable` produces `{bytes, committed}` from a single serialization —
`committed` is the parse of exactly those bytes and is the answer every
caller receives, first call and replay alike, owned by nobody. And
`withSecret` captures the `then` continuation once and assimilates THAT
callable with its original receiver, so the release cannot happen before the
act it belongs to settles. A throwing getter still lands in the synchronous
cleanup: a value whose classification failed was never handed to anyone, so
nothing else will ever release it.

### Recorded

One mutation left the suite green and should not have a test written for it:
re-parsing the durable bytes per caller is an EQUIVALENT implementation —
each call would hand back its own unowned copy of the same bytes, so
canonical, byte-stable and nobody's-alias all still hold. Pinning my
arbitrary choice with a regression would assert an implementation detail
rather than a property.

## Independent foundation round-seven re-review — 2026-08-22 (baton.codex)

**Confirmed corrected:** the first successful transaction returns the parsed
durable representation later retries replay, without a second serialization
or caller-owned alias. `withSecret` captures and uses one continuation,
preserving resolve/reject lifetimes and synchronous getter-failure cleanup.
The focused corrected baseline is 75/75.

**Observed — changes requested:** `forgetSecret` says its boolean reports
whether the value is now gone and that a pinned value never is. Releasing the
last dynamic registration of `GOLDEN_BEARER` returns `true` even though the
pinned registry correctly keeps the durable-secret guard active. The security
boundary holds, but the exported lifecycle answer contradicts it.

The exact correction boundary and P2 severity are in
`review-2026-08-22T19-49-19Z.md`. One additive regression fails
deterministically; focused evidence is retained in
`evidence/review-foundation-round7-2026-08-22.txt`. Return “gone” after the
last dynamic release only when the value is not pinned.

## Round-7 foundation correction — 2026-08-22

One P2, and worth pinning despite being small.

**AN EXPORTED ANSWER ABOUT A GUARD MUST AGREE WITH THE GUARD.**
`forgetSecret` reports whether a value is still live. It deleted the last
dynamic registration and reported "gone" without consulting the pinned
register, while the guard went on refusing the value — correctly. Nothing
leaked. What was wrong is that a caller could act on a report the enforcing
code contradicts, and a boundary whose description disagrees with its
behaviour is worse than one with no description: the disagreement is only
discovered by whoever trusts it.

The regression asserts AGREEMENT rather than the literal boolean, in both
directions. A boolean has two ways to be wrong, and always answering "still
live" would satisfy the reported case while breaking every ordinary release.

## Independent foundation round-eight re-review — 2026-08-22 (baton.codex)

**Confirmed corrected:** releasing the final dynamic registration of the
pinned golden bearer now reports `false`, matching the still-active guard.
The focused corrected baseline is 77/77.

**Observed — changes requested:** the same current-liveness result still
disagrees with the guard on an ordinary unbalanced release. After the final
owner is released, a second `forgetSecret` call changes no state and returns
`false`, while the guard correctly permits the already-gone value. Round
eight's explicit agreement rule therefore holds for the last-owner and pinned
cases but not the early no-owner branch.

The exact P2 correction boundary is in
`review-2026-08-22T20-00-37Z.md`. One additive regression leaves the focused
gate at 77/78; evidence is retained in
`evidence/review-foundation-round8-2026-08-22.txt`. When no dynamic owner
exists, report gone exactly when the value is not pinned, without changing
the inert state transition.

## Round-8 foundation correction — 2026-08-22

One P2, and it is the round-seven correction's other branch.

**A LIVENESS ANSWER IS ABOUT THE VALUE, NOT ABOUT THE CALL.** `forgetSecret`
reports whether the value is live now. Its inert branch — no dynamic owner to
release — returned `false` unconditionally, so releasing an ordinary value
twice claimed "still live" while the guard, correctly, permitted it. The call
really is state-inert; that is a fact about the transition and not about
liveness, and conflating them is what produced the same contradiction twice
in the same function.

### Recorded

Both of the reasons this survived a round are mine. The agreement case I added
last round stopped at the last owner and never asked the branch that answers
when there is none. And an earlier case of mine ASSERTED the wrong answer —
`false` after the final release — so the suite was arguing for the defect. A
test that pins the wrong answer is worse than a missing one.

Three mutations now cover the three branches separately: a boolean has as many
ways to be wrong as it has branches, and a reported case pins one of them.

## Independent foundation round-nine re-review — 2026-08-22 (baton.codex)

**Confirmed corrected and foundation slice signed off:** the no-dynamic-owner
branch now reports current liveness rather than whether the call found an
owner: an ordinary already-gone value returns `true`, while the permanently
pinned golden bearer returns `false`. The branch is state-inert in both cases.
Together with the nested-owner and last-owner branches, `forgetSecret`'s result
now agrees with the durable-secret guard across ordinary and pinned values.

The focused contract/store baseline is 78/78, the retained agreement case
visits every release branch, and no new foundation finding remains. Exact
review scope and evidence are in `review-2026-08-22T21-05-52Z.md` and
`evidence/review-foundation-round9-2026-08-22.txt`.

This sign-off is deliberately bounded to completed plan item 2. W2929 is not
complete: orchestration and agent-session/adapter plan items 3 and 4 remain
unstarted and are the next implementation boundary.

## Item 3, first half — the offer and the claim (2026-08-22)

**EVERY STEP IS A DURABLE FACT, BECAUSE THE QUESTION IS WHAT A RESTART CAN
TELL.** Reads before entropy, so a refused offer never mints a secret. The
per-Work CAS in the database, because two manager processes both pass a check
made outside the write. The verifier stored and the bearer returned only after
the commit. Acceptance consuming the verifier — single-use across acceptance,
decline and expiry alike — freezing the intent, deriving the fixed claim
operation id, and storing a settlement deadline SEPARATE from expiry.

**A LOST RESULT MAY ONLY BE OBSERVED BEFORE ITS DEADLINE.** A read saying
"not committed" proves only its own instant: the submitter may already have
passed its preconditions and be about to commit. Retiring early could close an
identity the authority is still going to honour, and the manager would then
record a refusal for a claim that won. At or after the deadline the
submitter's window is over and retirement is safe; positive evidence that the
claim refused is an answer rather than a guess and retires immediately; and
every path ADOPTS an existing retirement's bound disposition, because whoever
retired the identity first decided what it means.

**THE RESTART ASYMMETRY IS THE POINT.** An issued offer from a prior
incarnation is not honoured — nothing durable says its bearer was delivered.
An accepted one is recoverable, because acceptance is what froze the
authorization and the operation. And only ANOTHER incarnation's offers are
abandoned: managers coordinate through one store, so abandoning on identity
alone would let one live manager destroy another's work.

### Recorded

**A signed-off line changed.** `validateOfferDecide` compared the verifier
with `!==`, which exits at the first differing byte — on the one comparison
that decides whether authority is taken. It is `timingSafeEqual` now. I wrote
a second constant-time compare in `offers.mjs` first and removed it: two
comparisons where one exits early leaves the leak exactly where it was.

**A tautological case.** Asserting the stored operation id equals what the
same function returns is satisfied by any implementation. The property is that
a later incarnation derives it from the durable row alone, and that is what is
asserted now.

**A leaked fixture family.** The first version of this suite minted its own
temporary roots and left twenty behind, found by running the gate under a
bracket rather than by reading the code.

## Independent item-3a review — 2026-08-22 (baton.codex)

**Changes requested.** The scripted session hid two mismatches with the real
authority: acceptance stores no fixed authority signature, so committed-late
settlement collides, and claim/settlement results are direct assignments while
the manager reads a nonexistent nested `assignment` member and durably records
`null`. Offer issuance also accepts a participant different from the bound
session and makes the required certified-profile comparison optional.

Expiry only throws, leaving the offer nonterminal, its verifier unspent and
the Work's unique live-offer slot permanently occupied. Issuance replay mints
a new bearer before replaying the first verifier and signs only three of the
durable operands, so it can return a bearer/verifier mismatch and silently
replay a changed policy. Finally, the shared terminal helper updates
`accepted` as well as `issued`; a decline or restart abandonment acting from a
stale issued read can overwrite another manager's accepted authorization.

Seven additive regressions reproduce the executable failures. Exact findings,
correction boundary and evidence are in
`review-2026-08-22T21-36-26Z.md` and
`evidence/review-offer-claim-slice-2026-08-22.txt`.

## Item 3a correction — 2026-08-22

**A DOUBLE CAN AGREE WITH AN IMPLEMENTATION ABOUT A SHAPE NEITHER SHARES WITH
THE AUTHORITY.** Two of the six findings were exactly that: the claim
signature stored as NULL and passed as `undefined`, and the assignment read as
a member of a result that IS the assignment. My scripted session returned the
shape my code expected, so both suites agreed with each other and neither
agreed with `V12Session`. The corrections are to use the authority's own
`claimSignature` — imported, not restated, because a third copy of a signature
rule is a third thing that can drift — and to record what the authority
actually returns. The regressions now drive the whole path, and both
settlement windows, through a real session.

**AN AUTHORIZATION IS BOUND TO THE IDENTITY THAT WILL SPEND IT.** The
participant comes from the session's binding; an operand that disagrees is
refused before entropy, and a session with no binding is refused outright.

**EXPIRY IS A SETTLEMENT.** Throwing left the row `issued` with an unspent
verifier holding the per-Work slot, so the Work could never be offered again
and the bearer stayed replayable against the pinned single-use rule.

**EVERY ISSUED-ONLY TRANSITION CASes FROM `issued` ALONE.** Both callers act
from an earlier read, and a stale decline or abandonment that won would
destroy the durable authorization and fixed claim identity acceptance froze.

**CERTIFICATION CANNOT BE OMITTED.** A check conditional on its argument being
supplied is not a boundary — and the fixtures that omitted it are how it
survived. The control store's own row is preferred, an explicit assertion may
not contradict it, and absence of both is refused before entropy.

**AN OPERATION IDENTITY THAT IGNORES OPERANDS IS NOT AN IDENTITY.** The issue
signature covers every durable operand. And an exact re-issue refuses: the
bearer existed only in the process that minted it, so no later call can
reproduce it, and returning one that does not derive the stored verifier hands
back a secret the holder cannot use and cannot tell is unusable.

### Recorded

The issued-only CAS is UNWITNESSED — acceptance spends the verifier and the
verifier check refuses before the CAS is reached, so no reachable path drives
it today. It stays as defence for the callers the rest of item 3 will add.

The replay guard was green against the retained case, which permits either a
throw or a matching pair; a case of mine pins the answer.

## Item 3a correction re-review — 2026-08-22

**Confirmed corrected:** the fixed authority claim signature, direct
assignment shape, participant/session binding and unavoidable certification
all hold through the real-session boundary. Two reviewer-owned deterministic
interleavings now reach the issued-only decline and restart-abandonment CASes;
both lose without overwriting the concurrent acceptance. This supersedes the
correction note's statement that the predicate was unwitnessed.

**Confirmed still open:** the exact-reissue precheck is outside the journal
transaction. Two issuers can both observe a miss and mint; the winner commits,
then the loser's `transact` replays the winner's durable result and the caller
returns that result beside its own bearer. The sequential guard therefore does
not close the original bearer/verifier mismatch under concurrency.

**Confirmed still open:** TTL does not itself settle an issued offer. Expiry
is reached only while handling a late decision, so an elapsed offer whose
worker never answers remains `issued`, keeps an unspent verifier and occupies
the per-Work partial unique index indefinitely.

**Confirmed still open:** the issue signature omits the durable
`authority_uuid` binding. Reusing the same issue identity against another
authority is reported as an exact reissue rather than the required operation
collision, contradicting the recorded full-effective-signature rule.

Five additive re-review cases are retained: two passing CAS interleavings and
three failing reproductions. Exact findings and evidence are in
`review-2026-08-22T22-01-32Z.md` and
`evidence/re-review-offer-claim-2026-08-22.txt`.

## Item 3a, second correction — 2026-08-22

**THE DECIDING REPLAY IS THE ONE INSIDE THE TRANSACTION.** An optimistic check
before minting answers the sequential case and is worth having, but it is not
the decision: two concurrent exact issuers both pass it, and the loser was
handed the winner's committed record and returned it beside its own bearer.
The record is compared with what this call's bearer derives; a mismatch means
this call lost, and the answer carries no secret. **This is the second time I
have corrected the sequential shape of a race and left the concurrent one** —
the pattern worth remembering is that a pre-check and a decision are different
things, and only one of them is the boundary.

**A BOUND THAT NEEDS A MESSAGE FROM THE PARTY IT BOUNDS IS NOT A BOUND.**
Expiry was reachable only from a late decision, so an offer whose worker never
answered held the per-Work index forever with an unspent verifier.
`expireOverdue` is manager-owned time: it runs at reissue and at restart
recovery and needs nobody's cooperation. An elapsed offer settles VISIBLY as
`expired`, so an audit can tell it from a decline and from an offer that never
existed.

**A CHANGED DURABLE OPERAND IS NOT AN EXACT REPLAY.** The issue signature
carries the full authority-scoped Work binding, not the local id alone.

### Recorded

One mutation is INERT rather than uncaught: making the sweep select `accepted`
rows changes nothing, because the issued-only CAS refuses them. Two guards
cover one property and the second neutralises the mutation — recorded rather
than papered over with a test for a difference that does not exist.

## Item 3a second-correction re-review — 2026-08-22

**Confirmed corrected:** passive TTL settlement releases and visibly expires
silent offers, including recovery; the issue signature carries the durable
authority UUID; and concurrent issuers with different bearer values no longer
return an unusable pair.

**Confirmed still open:** the post-transaction check infers replay provenance
from `record.verifier !== verifier`. If two concurrent exact issuers receive
the same injected bearer, the journal loser has the same verifier and returns
successfully. The pinned exact-reissue contract requires the loser to refuse;
effectively-once provenance must come from whether this transaction committed
or replayed, not from probabilistic bearer uniqueness.

One additive regression fails deterministically. Exact finding and evidence
are in `review-2026-08-22T22-14-59Z.md` and
`evidence/review-offer-claim-round3-2026-08-22.txt`.

## Item 3a, third correction — 2026-08-22

**THE DECISION IS THE ONLY THING THAT KNOWS WHETHER IT DECIDED.** Provenance
was inferred by comparing the returned verifier with the one this caller's
bearer derives: inequality proves a loss, and equality proves nothing, because
two exact issuers can receive the same injected bearer. Effectively-once then
rested on a probabilistic property of the secret source rather than on the
journal.

`transact` runs the action only when it did not replay, so the action setting
a flag IS the transaction boundary reporting which happened. The verifier
comparison stays with a different job — if this call committed, the row must
derive from the bearer it minted, which is a store-defect invariant and not a
decision.

### Recorded

Three rounds on one race, and my error kept the same shape: answering "did
this call win?" with evidence NEAR the answer rather than the answer. First a
check placed before the decision; then a check reading what the decision
produced. A pre-check is not a decision, and neither is its output.

## Independent item-3a third-correction re-review — 2026-08-22 (baton.codex)

**Signed off:** the action-execution marker now deterministically distinguishes
this call's commit from a journal replay. The retained same-bearer interleaving
refuses the transaction loser even though its verifier equals the winner's;
the positive first-issue case confirms a real commit is not falsely refused.
Verifier equality remains only a post-commit integrity invariant.

The added sequential-reissue case is intercepted by the optimistic replay
precheck in the current implementation, so it pins the public refusal but is
not independent evidence for the marker branch. That precision does not leave
a functional coverage gap because the concurrent same-bearer case and the
positive first-commit case exercise the marker's two outcomes.

The focused offer suite is 43/43, the full v12 gate is 282/282, all four design
models pass at 64/24/74/56, and whitespace is clean. Exact review scope and
evidence are in `review-2026-08-22T22-21-52Z.md` and
`evidence/review-offer-claim-round4-2026-08-22.txt`.

This sign-off remains bounded to plan item 3a. The rest of item 3 and all of
item 4 remain unimplemented; W2929 is not complete.

## Item 3, second slice — activation and runtime start (2026-08-22)

**ACTIVATION BEFORE ANYTHING WRITABLE.** The live assignment is compared field
by field with the one the claim recorded, and a stale or ended one is refused
where nothing has been started. After one writable adapter call the same
refusal would leave a runtime nobody is authorized to own. The manifest is
fixed once, so a second activation naming a different assignment cannot
silently re-point the attempt.

**RECORD BEFORE CALLING.** `start-requested` is durable before the adapter is
touched. The alternative leaves a crash window with no trace that a runtime
may exist, and the next incarnation starts a second one. Recording first can
only OVER-report, and reconciliation resolves that by looking — which is the
asymmetry that makes the order obvious once stated.

**ZERO IS NOT ABSENCE.** "The adapter reports nothing" and "nothing exists"
are different facts. A retry needs positively proven absence; otherwise the
attempt waits. Two runtimes for one assignment is the failure the whole
ordering exists to prevent, so ambiguity costs a wait rather than a duplicate.

**IDENTIFICATION IS BY LABELS, NOT BY THE ADAPTER'S ID.** An id the adapter
minted proves only that something answers to it. Mismatch or multiplicity
cancels rather than starting another: two runtimes under one assignment's
labels means something already went wrong, and a third compounds it.

**UNCERTAINTY IS NOT AN OUTCOME.** `uncertain` never becomes `destroyed`.
Inferring destruction from a failure to look would let a manager report a
cleaned-up runtime that is still executing somebody's code. The one permitted
reset is narrow and explicit — only reconciliation that has proven absence may
take an axis back, because only it knows nothing is owed.

### Recorded

A case of mine walked the whole `execution_runtime` enum to prove every
declared value is reachable, and that walk passes through the one transition
the axis rule forbids. The two rules meet exactly there. It skips that step
now and says why — writing reachability and refusal as separate cases would
have hidden the meeting point entirely.

## Independent item-3 activation/runtime-start review — 2026-08-22 (baton.codex)

**Changes requested.** Activation is not tied to this attempt's committed
claim, ignores the participant-bound session, persists no assignment
participant, compares only Work/generation on replay, and therefore labels no
full four-part assignment. Attempt creation's operation signature also omits
durable adapter/input/policy/image/toolchain operands.

Runtime start writes only an unjournalled axis value and hands the adapter no
stable operation identity. Reconciliation accepts caller-authored
`absenceProven: true` as positive evidence, permits a later inspection to
overwrite the fixed runtime id, and ignores the exact minted runtime when it
returns with wrong labels. Observation monotonicity is based on enum order,
so one terminal disposition can replace another; exported `allowReset`
bypasses it entirely; and the read/check/unconditional-write sequence lets a
stale connection overwrite a stronger concurrent observation.

Twelve additive regressions reproduce the seven correction boundaries. The
focused attempt gate is 13 passed and 12 failed out of 25; the full gate was
not repeated after that blocking result. Exact severities and evidence are in
`review-2026-08-22T22-34-55Z.md` and
`evidence/review-attempt-slice-2026-08-22.txt`.

## The activation/runtime-start slice, corrected — 2026-08-22

Seven P1s, and they share a shape worth naming: **a check can be ABOUT the
right thing without being BOUND to it.** An assignment that is live somewhere
is not this attempt's claim. An enum's order is not a transition order. A
boolean that says a proof happened is not the proof.

**ACTIVATION BINDS THREE THINGS.** The session's binding, this attempt's own
committed claim, and the authority's live assignment must all agree. Any two
agreeing is how a foreign session or a replayed activation gets in. All four
assignment fields are persisted, compared and labelled — a manager that stored
three of four could not compare the fourth, and two participants' runtimes on
one Work and generation were indistinguishable by label.

**A STATE LABEL IS NOT AN EFFECTIVELY-ONCE ACT.** Runtime start commits one
fixed, fully signed operation and hands its identity to the adapter, so a
restart and the adapter settle the same act rather than two adjacent ones.

**A PROOF THE CALLER WRITES IS NOT A PROOF** — the third time this shape has
appeared in this Work. Positive absence needs certified adapter evidence,
which item 4 owns, so the retry path is closed and the refusal names the slice
that will open it.

**ENUM ORDER IS NOT A TRANSITION ORDER.** A vocabulary lists what an axis may
SAY; only a transition map says what may FOLLOW what. Terminal alternatives are
immutable, because `completed` and `unable` are different answers rather than
successive stages — and there is no public reset, because a monotonicity a
caller can switch off is not one.

**DECIDE INSIDE THE WRITE.** The transition is compared by the UPDATE itself,
in a savepoint (not a transaction — `observe` is also called inside a
journalled operation, and a nested BEGIN would refuse). A concurrent writer is
refused as a typed `runtime-observation` error rather than a raw SQLite one: a
caller that must handle both will eventually handle neither.

### Recorded

Four mutations passed at first and each earned a different answer. One was
witnessable and is now witnessed. Two are backed by the DECIDING guard — the
SQL compare-and-swap and the lock — with the JavaScript check redundant, so a
case drives the database's answer directly. One is unwitnessable by
construction, because an attempt has exactly one claimed offer, and is named
as defence rather than counted as covered.

Two of the review's retained cases also corrected my MODEL: a cold start can
discover a running or destroyed runtime directly, because at restart the local
axis is `not-started` while a runtime may already exist.

## Independent correction re-review — 2026-08-22 (baton.codex)

**Changes still requested.** The original 27 focused cases pass, but six
additive cases expose four remaining P1 boundaries and one P2 diagnostic
boundary. `offers.runtime_attempt_id` is not unique, so `claimOf(...).get()`
can choose arbitrarily between two claimed offers instead of proving this
attempt's one claim. Observation source identity is consulted only after the
current-value and transition shortcuts, so an exact duplicate refuses after
later progress while a conflicting duplicate can disappear as an inert
repeat.

Reconciliation also cannot enter cancellation when multiplicity is discovered
after an earlier `uncertain` observation, and a concurrent different attachment
surfaces the shared attach operation's signature collision before the SQL CAS
can preserve the winner and enter mismatch cancellation. Finally, `observe`
rewrites every non-contract SQLite failure as competing-writer state
regression, including a deterministic non-locking abort.

The retained 309 v12 cases remain green; the full gate is 309 passed and 6
failed out of 315. Exact severities, correction boundaries and evidence are in
`review-2026-08-22T22-53-46Z.md` and
`evidence/re-review-attempt-slice-2026-08-22.txt`.

## The activation/runtime-start slice, second correction — 2026-08-22

**AN INVARIANT ONLY THE WRITER MAINTAINS IS NOT AN INVARIANT.** `claimOf`
assumed one claimed offer per attempt because the allocator only ever makes
one — and the store had no constraint saying so, while the store is what the
reader reads. I called that branch unwitnessable by construction last round;
the construction lived in the wrong place. There is a unique index now AND a
reader that fails closed for a store written before it, and the fail-closed
branch is witnessed by building the damaged store it defends against.

**A DURABLE IDENTITY IS RESOLVED BEFORE TODAY'S STATE.** What a source
identity already said is a fact about that identity. Consulting today's axis
first refused an exact duplicate once the axis advanced, and let a different
observation reuse one identity whenever the axis already held the requested
value — the pinned rule inverted in both directions.

**AN AMBIGUOUS OBSERVATION MUST NOT DISABLE A SAFETY RESPONSE.** The
cancellation intent is reachable from every nonterminal runtime state, because
mismatch and multiplicity can be discovered from any state in which the
manager is still looking. That is separate from the rule about destruction,
which uncertainty still never proves.

**TWO ATTACHMENTS ARE TWO ACTS.** Sharing one operation identity made a stale
manager's second attachment read as a botched retry of the first, so it
surfaced an operation collision instead of the mismatch cancellation. A lost
race re-reads the fixed identity, preserves it, and cancels for the different
runtime it saw.

**A WRONG DIAGNOSIS IS WORSE THAN A RAW ERROR.** Only a locked database means
contention; a constraint, a trigger abort or a disk fault would have inherited
a portable meaning and a retry policy belonging to something else. A caller
can see that a raw error is unclassified; it cannot see that a confident one
is wrong.

### Recorded

One mutation of mine was not faithful and passed for that reason — it moved
where a value was read rather than the ordering that matters. And the
attach-identity mutation is EQUIVALENT rather than uncovered: the same handler
catches both the collision and the CAS refusal, so the outcome is identical by
a different route. The runtime-scoped identity is still correct; it is simply
not what decides.

## Independent second-correction re-review — 2026-08-22 (baton.codex)

**Changes still requested.** All 35 delivered focused cases pass, including
the six retained from the prior review, but three additive cases expose two
remaining P1 boundaries and one P2 diagnostic boundary.

The durable observation lookup now precedes current-state logic, but an
adapter-sourced observation of an already-current value returns success without
writing its source identity. A different observation can then reuse that same
incarnation/sequence and commit. The execution map says cancellation is
reachable from every nonterminal state but omits `stopping`, so multiplicity
discovered during an in-flight stop throws state regression instead of
returning the pinned cancellation response. Finally, the narrowed SQLite
classifier still accepts any free-form error message containing `busy`, so
application prose can manufacture the database-lock diagnosis.

The retained 317 v12 cases remain green; the full gate is 317 passed and 3
failed out of 320. Exact severities and evidence are in
`review-2026-08-22T23-07-46Z.md` and
`evidence/re-review-attempt-slice-round3-2026-08-22.txt`.

## The activation/runtime-start slice, third correction — 2026-08-22

**AN IDENTITY'S MEANING MUST NOT DEPEND ON WHERE THE AXIS ALREADY WAS.** Last
round the durable source identity was consulted too late; this round it was
resolved first but not *consumed* when the observation changed nothing — so an
inert sourced observation left its `(attempt, incarnation, source_seq)`
reusable and a different observation committed under it. The conflict rule bit
only when the first observation happened to move state, which is the same
inversion arriving from the other side. Every accepted sourced observation
consumes its identity now. A manager-internal repeat stays inert because it
mints a fresh sequence and consumes nothing another caller could reuse.

**THE SAFETY RESPONSE IS A DECISION, NOT A TRANSITION.** `stopping` had no
cancellation response, but declaring `stopping -> cancel-requested` would move
the axis BACKWARDS to re-announce an intent the runtime is already carrying
out. Cancellation is idempotent for a stop in flight: the decision is
returned, the axis is left where the runtime actually is. `destroyed` stays
excluded and is named as excluded — an adapter still listing runtimes for a
destroyed attempt is a contradiction, not a cancellation this manager can
perform, and reporting it as one would promise an act that never happens.

**A RESULT CODE IS THE SYSTEM'S ANSWER; A MESSAGE IS THE APPLICATION'S.**
Matching `busy` as a substring of free-form prose gave a trigger's own abort a
database lock's portable meaning and retry policy. SQLite's `errcode` is
structured — the low byte is the primary code — and only `SQLITE_BUSY` and
`SQLITE_LOCKED` mean contention. Measured against the real boundary rather
than reasoned from the wording.

### Recorded

One mutation makes the reviewer's case PASS while failing only my own: the
decision and the axis are two claims, and pinning one does not pin the other.
And the mutation for the contention classifier showed its positive side was
already witnessed by an earlier case, so my added case is a second direct
witness rather than the first witness of anything.

## Independent third-correction re-review — 2026-08-22 (baton.codex)

**Signed off for the activation/runtime-start slice through plan item 3i.**
All three prior findings are corrected. A sourced no-change observation now
consumes one durable identity and replays exactly; a manager-internal repeat
remains inert. Cancellation discovered while a stop is in flight returns the
safety decision without rewinding the axis or advancing its observation
sequence, while `destroyed` remains a terminal contradiction. SQLite
contention is classified only from the structured BUSY/LOCKED primary result
codes, with both trigger-abort and genuine-lock paths driven.

The focused attempt suite passes 41/41 and the full v12 gate passes 323/323.
This sign-off is bounded: cancellation ordering, output freeze/intake/cleanup
and all of item 4 remain unimplemented and unreviewed. Review and evidence:
`review-2026-08-22T23-21-33Z.md` and
`evidence/re-review-attempt-slice-round4-2026-08-22.txt`.

## Item 3, third slice: cancellation ordering — 2026-08-22

**FENCE, THEN STOP.** Until the authority has fenced the generation the
assignment is still live, so a runtime stopped first is a worker torn out from
under an assignment the authority still believes is executing. `session.cancel`
is called first and everything else runs after it returns; a refused fence
stops nothing and moves no axis.

**A CRASH BETWEEN TWO BOUNDARIES MUST BE ANSWERABLE.** The manager journals
its cancellation intent before asking the authority, and both operation
identities are derived from the attempt and its fixed assignment so a restart
names the act it already performed. They are deliberately DIFFERENT strings:
§4.2 says success at one boundary does not imply success at the other, and one
shared identity would invite reading either journal's row as evidence of the
other's.

**LIVENESS IS THE AUTHORITY'S DECISION.** There is no pre-check asking whether
the assignment is still live — asking first and acting on the answer is a
read-then-write race wearing a guard's clothes.

**ORDERING CANNOT BE ASSERTED FROM RESIDUE.** Stopping-then-fencing and
fencing-then-stopping leave identical rows. The doubles share one trace so the
sequence itself is what the cases pin, and the whole path is driven once
against a real authority so the fence, the ended assignment and the typed gate
are the authority's own facts rather than a double's agreement with the
implementation.

**THE GATE THIS INSTALLS IS NOT SATISFIED HERE.** The authority takes only
positive absence naming the exact runtime, or a certified-isolation policy.
That is the same claim the retry path is closed for until item 4 defines
certified adapter evidence, and answering one question two ways would be worse
than answering it late. Agent-side quiescence is not that evidence.

### Recorded

A destroyed runtime refuses the reconciliation `cancel` DECISION and merely
leaves nothing to stop for the cancellation ACT. That is two rules, not an
inconsistency — one reports what an inspection found, the other performs a
cancellation at the authority — and both keep the axis where the runtime is.

The first ordering fixture started a runtime the adapter never listed, so
nothing attached and every ordering case passed while stopping nothing. A
fixture that does not establish its own precondition proves whatever it likes.

## Independent cancellation-slice review — 2026-08-22 (baton.codex)

**Changes requested.** The authority-first fence, refusal behavior, separate
stable operation identities and real-authority path are accepted. Three
boundaries remain open. First, the implementation orders only runtime stop;
the agent-cancellation act required by this finding is absent, so item 3k is at
most the runtime-side portion until the provider boundary exists. Second,
`orderStop` discards the adapter's result and reports `stopped:true` merely
because it made the call, manufacturing a positive fact while the durable axis
still says only `cancel-requested`. Third, PLAN item 3k says a stop already in
flight is not re-ordered, while implementation and its test require the
opposite. The current rule must be made singular and explicit.

The additive stopped-fact regression is the sole failure in both gates:
focused 53/54 and full v12 335/336. Review and evidence:
`review-2026-08-22T23-40-54Z.md` and
`evidence/review-cancellation-slice-2026-08-22.txt`.

## The cancellation-ordering slice, corrected — 2026-08-22

**A DEFERRED BOUNDARY CAN SWALLOW THE THING BEING BUILT.** The acceptance
orders agent cancellation AND runtime stop after the fence; I built the
runtime half and deferred the agent to item 4. Item 4 owns what a conforming
agent must BE. Where its cancellation sits in the ORDER is item 3's, and that
was the entire subject of the slice. The agent is an injected boundary now,
ordered between the fence and the stop — first, because an agent told to stop
after its runtime is already going away never hears the order, and cooperative
shutdown is the only thing asking it buys over a kill.

**REACHING A BOUNDARY IS NOT EVIDENCE OF ITS EFFECT.** Reporting
`stopped: true` because `adapter.stop` returned is the caller-authored
`absenceProven` mistake arriving from the manager's own side. The manager
reports what it knows — that it ORDERED the acts — and passes each settlement
through uninterpreted. Positive quiescence arrives as an observation or not at
all.

**THE PARAMETER ORDER IS THE ACT ORDER**, so the boundary shapes are checked:
two adjacent injected objects are easy to swap, and a swap must refuse rather
than cancel the wrong boundary first.

### Recorded

Plan item 3k said the stop order is not repeated for a runtime already
`stopping`, while the code repeats it and its own regression requires the
repeat. The drafting was mine and the code is right — the AXIS is not rewound,
the ORDER is re-issued under one operation identity — and the plan carries a
dated correction rather than a silent rewrite. A plan and an executable
acceptance cannot hold opposite live requirements; when they do, one of them
is a claim nobody is checking.

## Independent cancellation-correction re-review — 2026-08-22 (baton.codex)

**Changes requested.** The three prior findings are corrected on their
exercised paths. One post-fence failure path remains: `agent.cancel` is called
directly before `adapter.stop`, so an agent transport exception exits the
function and suppresses runtime stop after the authority has already fenced
and ended the assignment. Persistent inability to request cooperative agent
cancellation must not veto the configured runtime stop/force-stop path.

The additive injected-failure regression is the sole failure in both gates:
focused 57/58 and full v12 339/340. Review and evidence:
`review-2026-08-22T23-55-38Z.md` and
`evidence/re-review-cancellation-slice-2026-08-22.txt`.

## Independent cancellation failure-handling review — 2026-08-23 (baton.codex)

**Changes requested.** The prior post-fence P1 is corrected for ordinary
`Error` failures, and the absence of durable agent-failure evidence is
explicitly and acceptably deferred to item 4's agent-session evidence surface.
One value/sentinel collision remains: `agentFailure = null` means no failure,
but JavaScript also permits `agent.cancel` to throw `null`. That failure is
caught, runtime stop is ordered, and then the failure is silently mistaken for
absence and an ordinary success answer returns. Failure presence must be
tracked independently of the value that was thrown.

The additive sentinel regression is the sole failure in both gates: focused
60/61 and full v12 342/343. Review and evidence:
`review-2026-08-23T00-05-09Z.md` and
`evidence/re-review-cancellation-round3-2026-08-23.txt`.

## The cancellation-ordering slice, second correction — 2026-08-22

**A COOPERATIVE REQUEST IS NOT A PRECONDITION FOR THE FORCEFUL ONE.** Putting
agent cancellation in front of the runtime stop put a failure in front of it
too: a throwing agent left the function before the stop was ordered, with the
authority already fenced. Persistent agent unreachability is a REASON to stop
the runtime, not a reason to leave it running. The failure is captured, the
stop is ordered, and the failure is then re-thrown unchanged — the order is
preserved and the classification stays the caller's.

**NEITHER FAILURE MAY HIDE THE OTHER.** When both post-fence boundaries throw,
an `AggregateError` carries both in call order. Letting the later one
propagate alone would be this boundary choosing which failure the caller is
entitled to see, which is the same shape as summarizing a settlement into a
fact.

**ADDING AN ACT ADDS ITS FAILURE MODE.** The defect was created by the
previous correction, one round earlier, and the question that would have found
it is the obvious one: what happens when the thing I just put first does not
work?

### Recorded

One mutation is EQUIVALENT rather than uncovered — the failure path throws
before the return, so a settlement assigned there is dead code. It also
exposed a case title of mine that claimed more than the case pinned, and the
title is corrected.

A failed agent cancellation is visible to the CALLER and is not durable; there
is no agent-session evidence table yet, and that gap is named rather than
glossed.

## The cancellation-ordering slice, third correction — 2026-08-23

**A VALUE THAT ALSO MEANS ABSENCE CANNOT CARRY PRESENCE.** `agentFailure =
null` meant both "nothing was thrown" and "`null` was thrown", and JavaScript
lets a boundary throw any value — so an agent that threw `null` had its
failure silently dropped and could not reach the aggregate beside a
simultaneous runtime failure. Presence is a boolean of its own; the variable
carries only the thrown value.

**A RECORDED LESSON IS NOT A GENERALIZED ONE.** `ControlStore.replay` already
carried this exact correction in this exact wording, from an earlier round of
this same Work — `null` answered both "no row" and "the result was JSON null".
I wrote the identical defect three modules later. Writing a lesson down where
it was learned does not carry it to the next place it applies; that is a
property of the reader, and the reader was me.

**AND ONE SIZE SMALLER, FOUND BY SWEEPING FOR THE SHAPE.** `?? null` on the
settlements collapsed "the boundary returned nothing" into "the boundary
returned null", contradicting the comment directly above it. Both are verbatim
now.

### Recorded

One mutation exists specifically because swapping which falsy value means
absence MOVES the defect rather than removing it, and only a case that throws
`undefined` can tell the difference. A test suite that pins one sentinel
blesses the next one.

## Independent cancellation-ordering sign-off — 2026-08-23 (baton.codex)

**Signed off for the cancellation-ordering slice through plan item 3n.** The
authority fence precedes agent cancellation and runtime stop; refusal reaches
neither later boundary; agent failure cannot suppress runtime stop; single and
dual failures remain visible; and failure presence is independent of any
thrown value. Settlements remain verbatim and are never promoted to positive
quiescence. Focused gate 64/64; full v12 gate 346/346.

This sign-off is bounded. Output freeze, intake, cleanup and item 4 remain
unimplemented. In particular, durable agent-session failure evidence remains
owned by item 4, and agent cancellation still cannot satisfy the runtime
quiescence gate. Review and evidence:
`review-2026-08-23T00-13-56Z.md` and
`evidence/signoff-cancellation-ordering-2026-08-23.txt`.

## Item 3, fourth slice: the output freeze — 2026-08-23

**GONE IS NOT FINISHED.** A seal describes a tree that has stopped changing,
so only a positive `quiescent` observation admits a freeze. `uncertain` is a
failure to look, and `destroyed` is a writer nobody watched stop — neither is
evidence that anything finished. The refusal uses the code already pinned for
this question, `runtime-observation.quiescence-unknown`, which names what is
missing rather than blaming the request.

**A GATE IS NOT A CHOICE.** The turn outcome gates the worker disposition and
never chooses it, and turn records belong to item 4. So the freeze requires a
terminal disposition to be already RECORDED and compares the declaration
against it, rather than accepting a turn outcome from its caller. The sealed
document must then say the same thing: three places must agree, because two
agreeing is how the third gets in.

**A READ ACROSS TWO STORES IS A PRECONDITION, NOT A PROOF.** The authority is
a different database; nothing this manager does makes "still live" and
"recorded frozen" one atomic fact. The window is minimized and then NAMED in
the code, and the design carries the residue elsewhere — ended-assignment
material is quarantined at intake rather than trusted at freeze.

**THE IDENTITY IS THE ACT; THE SIGNATURE CARRIES THE BYTES.** That is the
whole mechanism behind "the same digest replays; changed bytes under the same
identity refuse". An identity that varied with the bytes would make two
different results two different operations, and both would commit — the
opposite of an immutable record. It also means the replay path must admit an
already-`frozen` attempt, or a crashed manager's retry becomes a precondition
failure that hides the collision.

### Recorded

One mutation is EQUIVALENT rather than uncovered: recomputing the manifest
digest after `validateManifest` has already proved the declared one recomputes
changes nothing. It is kept for provenance — the stored number is a
computation rather than a copied claim — and the comment says so instead of
implying a guard.

A fixture that drove an axis "until it matches" silently reached a different
state than the one its case named. It walks a declared route now. A fixture
that searches for its precondition is a fixture that will one day assert about
somewhere else.

## Independent output-freeze review — 2026-08-23 (baton.codex)

**Changes requested.** Four acceptance boundaries remain open. The result's
`freeze_operation.signature_digest` is never compared with the exact
journalled freeze signature; exact record replay is hidden once the output
axis advances beyond `frozen`; the manager has no trusted input declaration
from which it could enforce “declared outputs only” or missing-required rules;
and schema 4 retains only a result summary/artifact subset rather than the
immutable full result manifest required for restart, intake and publication.

The positive-quiescence, recorded-disposition, cross-store-liveness,
manifest-validation and fixed-identity boundaries are accepted. Two additive
regressions are the only failures: focused 24/26 and full v12 370/372. Review
and evidence: `review-2026-08-23T00-30-49Z.md` and
`evidence/review-freeze-slice-2026-08-23.txt`.

## The output-freeze slice, corrected — 2026-08-23

**A DIGEST IS NOT A RECORD.** The store held `attempt.input_digest` and
`outputs.manifest_digest` and not one byte of either document. Freeze could
not compare a sealed result against the OUTPUT DECLARATIONS the input manifest
names, and intake, publication and every restart were left with a number and
nothing to replay or inspect. Both are the same fact — a validated document
this manager is holding — so one table keyed by the identifying digest answers
both. Retention is idempotent by construction, and a digest that would name
two documents is refused rather than overwritten.

**THE ID IS THE RETRY KEY; THE SIGNATURE IS THE BINDING.** Passing and
comparing only the operation id accepted any schema-shaped digest as the
echo of the freeze, and the fixture that "proved" the happy path supplied an
unrelated one. The whole identity crosses the boundary and both halves are
compared: an adapter handed only the key cannot echo a binding it never
received.

**THE DURABLE IDENTITY IS RESOLVED BEFORE TODAY'S AXIS — THE THIRD TIME.**
Once `output` advanced to `sealed`, an exact retry of a committed result
refused as a precondition instead of replaying the journal. The same defect
has now appeared in `ControlStore.replay`, in `observe`, and here. Writing the
lesson down in the module where it was found does not carry it to the module
where it is written next; that is a property of the reader.

**A COMPARISON THAT RUNS ONE WAY IS HALF A COMPARISON.** Every result output
must be declared, AND every declaration must be answered — a declaration
dropped from the result is not an answer to it. And the required-output rule
is conditioned on the disposition, because the pinned sentence has two halves:
a missing required output prevents a SUCCESSFUL result, while an inability may
return evidence without pretending the requested result exists.

### Recorded

One mutation makes the STRICTER rule — refusing a missing required output
under every disposition — and is still wrong, because the permission is as
pinned as the prohibition. A test suite that only pushes toward stricter
cannot see that.

The fixture's `INPUT` was `digest("input")`: a number naming no document,
which is precisely why nothing could be compared against a declaration. A
fixture whose constants mean nothing produces cases that check nothing, and it
passed for as long as the implementation agreed with it.

## Independent corrected-output re-review — 2026-08-23 (baton.codex)

**Changes requested.** The complete freeze identity, replay after later output
axis advancement, full result retention, and bidirectional name/type/status
comparison are accepted. Four trust boundaries remain: a retained result
manifest can be mistaken for the input declaration because loads validate
neither kind nor digest/key; declared output size/count/media constraints are
not enforced; result retention's `INSERT OR IGNORE` silently accepts an
existing digest with different bytes; and exact result replay still consults
current input-retention state before the committed operation journal.

Four additive regressions are the only failures: focused 39/43 and full v12
385/389. Review and evidence: `review-2026-08-23T00-49-18Z.md` and
`evidence/re-review-freeze-slice-2026-08-23.txt`.

## The output-freeze slice, second correction — 2026-08-23

**BEING AT THE NAMED KEY IS NOT BEING THE NAMED THING.** A loader that parses
a row and hands it back has checked that something is stored there, not that
it is what the caller needs. A retained RESULT manifest could be named as an
attempt's input declaration and its similarly shaped output rows read as
trusted declarations — with every individual operation in that sequence valid.
The kind is required at the call site now, validated on load, and re-bound to
its key: a guard on the way IN cannot see a document put there by a different,
equally legitimate call.

**ONE RULE, ONE PLACE.** The collision refusal lived in `retainManifest` and
the result path wrote `INSERT OR IGNORE` past it, so a durable row could
reference bytes its digest does not identify while the operation reported
success. Writing a rule in one function does not apply it to another writer of
the same table.

**A LIMIT THAT IS DECIDABLE HERE AND NOT DECIDED HERE IS A LIMIT NOBODY
ENFORCES.** The declared constraints were never read. Byte verification is
W2930's, but the counts, totals and media type are already inside the document
this boundary accepted — and an allow-list is read literally, including an
empty one, because permitting everything when it names nothing is a fail-open
reading of a rule written to close.

**MOVING THE CHECK THE REVIEW NAMED IS NOT MOVING THE BOUNDARY THE RULE IS
ABOUT.** The previous correction put the output axis behind replay and left
the declaration lookup in front of it, so an exact retry still depended on
current retention. The immutable identity comes first and everything about
today follows it.

### Recorded

One mutation was inert, and the reason improved the code: the guard that
skipped measuring an absent output was redundant with its own null handling —
until it was made to refuse the contradiction the schema permits, an output
reporting itself missing while carrying material. An inert guard is either a
decision waiting to be made or a line waiting to be deleted.

## Independent second-correction re-review — 2026-08-23 (baton.codex)

**Changes requested.** All four item 3r findings are closed: retained loads
prove kind and digest/key, result retention shares the collision refusal,
replay precedes current state, and declared limits are enforced. One adjacent
P1 remains. The symmetric status/material rule is incomplete: a result that
says a required output is `present` while carrying neither a content manifest
nor an artifact freezes successfully under `completed`.

The one additive regression is the sole failure: focused 50/51 and full v12
396/397. Review and evidence: `review-2026-08-23T01-02-53Z.md` and
`evidence/re-review-freeze-round2-2026-08-23.txt`.

## The output-freeze slice, third correction — 2026-08-23

**A STATUS WORD IS NOT MATERIAL.** An output reporting `present` with neither
a content manifest nor an artifact reference satisfied a REQUIRED declaration
under a completed disposition, because the required rule tested only the
status string and every limit was skipped when there was nothing to measure.
§8.4 binds "every declared output's content/tree digest AND artifact
reference": both are required for a present output, and the nullable members
exist so a MISSING output can say so — not so a present one can choose which
half to supply.

**ENFORCING ONE DIRECTION OF A TWO-DIRECTIONAL RULE, TWICE IN TWO ROUNDS.**
The previous round refused a missing output that carried material and left the
converse open. The round before that recorded "a comparison that runs one way
is half a comparison" — in this dossier, about this function. A lesson written
beside the code did not reach the next branch written under it.

**AN INERT BRANCH IS EITHER A DECISION OR A DELETION**, and this one became a
decision. Requiring both representations made the size fallback unreachable,
so both sizes are bounded by the declaration now: measuring only the tree
would leave the transported representation unbounded, and the constraint is
about the output rather than about whichever representation happened to be
there.

### Recorded

One mutation satisfies the review's own case — which drives NEITHER
representation — while accepting an output that supplies only one. A rule that
rejects just the empty case is satisfied by whichever half is cheaper to fake,
so each half is driven separately.

## Independent output-freeze sign-off — 2026-08-23 (baton.codex)

**Signed off for the output-freeze slice through plan item 3s.** The symmetric
status/material correction matches frozen worker-control SPEC §8.4: a missing
output carries neither representation and a present output binds both its
content manifest and artifact reference. Both declared sizes are bounded.
Together with the earlier corrections, the slice now closes assignment,
quiescence, disposition, complete operation identity, replay/collision,
typed retained-manifest, full-result durability, declaration completeness and
decidable constraint boundaries.

Focused gate 53/53; full v12 gate 399/399. This sign-off is bounded: intake,
cleanup, W2930's artifact-byte verification and all of item 4 remain open.
Review and evidence: `review-2026-08-23T01-12-35Z.md` and
`evidence/signoff-output-freeze-2026-08-23.txt`.

## Item 3, fifth slice: trusted intake and cleanup — 2026-08-23

**A HANDLE PASSED AND NOT USED IS A RULE ENFORCED BY GOOD INTENTIONS.** Intake
must never publish, so `recordIntake` is given no session at all. The rule is
kept by the shape of the boundary rather than by the discipline of whoever
edits it next — which is the difference between the invariants this Work has
had to correct and the ones it has not.

**RETENTION IS NOT ACCEPTANCE.** Whether intake wanted the material and where
the material went are two facts and are stored as two, because a REJECTED
draft that is RETAINED under policy is an ordinary outcome and one column
would make it unsayable.

**A DURABLE REFUSAL NEEDS AN IDENTITY THAT MOVES WHEN RE-EVALUATION BECOMES
LEGITIMATE.** The cleanup operation is derived from the intake state it was
evaluated against, so a retry while nothing has changed replays the refusal
the store already holds, and a decision by intake makes the next evaluation a
new act. A counter would have satisfied the sentence and been caller-authored.

**A POLICY TAKEN AS AN ARGUMENT IS A PROOF THE CALLER WRITES** — the fourth
appearance of that shape in this Work, and the fourth closure. The contract
admits a pinned discard policy as an alternative to the intake boundary; until
that policy is a durable fact this manager can read, only the intake boundary
opens destruction.

**ORDERED IS NOT DONE, AND STILL LIVE IS NOT OVER.** The adapter's settlement
is passed through uninterpreted and the cleanup axis moves only on a positive
`destroyed` observation. Destruction waits for the assignment to be ended or
fenced, because tearing out the runtime of an assignment the authority still
believes is executing is the cancellation ordering defect from the other end.

### Recorded

One mutation was not faithful and passed for that reason: it disabled one
disjunct of a four-way condition, leaving the clause the case actually drives
in place. A mutation that changes a line the test does not reach proves
nothing about the line it does.

## Independent intake/cleanup review — 2026-08-23 (baton.codex)

**Changes requested.** The delivered sixteen intake/cleanup cases remain
green, but four additive cases expose three P1 trust boundaries and one P2
schema boundary. Intake currently records a disposition without any sealed
output and stores no result-manifest identity, so the decision is not bound to
the exact material the frozen operation table requires. Intake prose bypasses
the durable-secret guard because `reason` is written to its own table while
the guarded journal result omits it. `settleCleanup` can mark cleanup complete
from a `destroyed` runtime observation without the recorded intake or durable
discard-policy gate. Finally, `retainUntil` accepts arbitrary text even though
it is durable deadline state.

The focused gate is 16/20 and the full v12 gate is 415/419; the four additive
review cases are the only failures. Exact severities, correction boundaries
and evidence are in `review-2026-08-23T01-29-05Z.md` and
`evidence/review-intake-cleanup-2026-08-23.txt`.

## The intake/cleanup slice, corrected — 2026-08-23

**A LOCATOR IS WHERE SOMETHING IS, NOT WHICH THING IT IS.** Intake required
only a fixed assignment and recorded an unbound locator, so a decision could
be made about material that was never sealed — and the slice's own fixture
proved it by deciding the fate of material that did not exist. The decision
names the immutable result it judged now, with a foreign key to the retained
bytes, and the fixture freezes real material through the real path.

**A SUMMARY THAT OMITS A COLUMN IS NOT A GUARD OVER THAT COLUMN.** The shared
durable-secret scan runs over an operation's serialized RESULT; the result
omitted `reason`, so a live bearer passed as prose committed verbatim. The
exact durable record is what is scanned, assembled before anything is written.

**ABSENCE DOES NOT DECIDE POLICY.** A destroyed-runtime observation proves the
runtime is gone. Whether the ended assignment's material was retained or
quarantined is a different question with a different answer, and letting the
first stand in for the second let cleanup complete with no intake decision at
all. Two gates, not one gate doing two jobs.

**A DEADLINE IS A DEADLINE OR IT IS NOT ONE.** A STRICT column constrains a
storage class, not a meaning, so the literal `tomorrow` was accepted as
durable scheduling state.

### Recorded

One mutation is BLUNT: writing a nonexistent result digest is refused by the
foreign key, which is the deciding guard, and it takes most of the suite with
it. That proves the constraint rather than the narrower claim that the
recorded digest is the one this manager sealed, so the narrower claim is
pinned by its own case.

## Independent intake/cleanup correction re-review — 2026-08-23 (baton.codex)

**Changes still requested.** All four item 3v findings are accepted as closed,
and the retained 423-case baseline is green. Two adjacent P1 durability
boundaries remain. `recordIntake` consults the current output row before the
operation journal, so an exact committed decision cannot replay — and a
changed retry cannot collide — after that index row is absent even though the
intake row still owns the digest and keeps its retained bytes alive.
`intakeOf` then authenticates only assignment fields: its new foreign key
proves that some manifest exists, not that its digest is the result the
committed decision recorded. A second valid result can be substituted and is
trusted by cleanup.

Focused gate 24/26; full v12 gate 423/425. Only the two additive re-review
cases fail. Exact correction boundaries and evidence are in
`review-2026-08-23T01-43-26Z.md` and
`evidence/re-review-intake-cleanup-2026-08-23.txt`.

## The intake/cleanup slice, second correction — 2026-08-23

**THE DURABLE IDENTITY BEFORE TODAY'S STATE — THE FOURTH MODULE.**
`ControlStore.replay`, `observe`, `recordFrozenResult`, `recordIntake`. Four
times the same rule, four times the same defect written fresh into the next
boundary. The fix that holds is structural rather than positional: an existing
decision already NAMES its material, so today's index is consulted only when
there is no decision to replay — which is exactly the case in which requiring
it can hide nothing.

**A FOREIGN KEY PROVES EXISTENCE, NOT IDENTITY.** The constraint says some
retained manifest exists under that digest; it says nothing about whether this
is the result the decision committed, so a row pointed at a second
individually valid result passed every check and reached cleanup. The journal
authenticates the row: its columns are reassembled into the exact durable
record and the recomputed signature is compared with the committed operation.
Writer and reader build that record in ONE place, or the two signatures are
merely two computations that agree today.

**A ROW DISAGREEING WITH ITS OWN DECISION IS NOT A CALLER REUSING AN
IDENTITY.** The mismatch is reported as `integrity.digest`; surfacing
`refused.operation-collision` would hand it a portable meaning and a retry
policy belonging to something else.

### Recorded

One mutation is MASKED rather than uncovered, and measuring it is the finding:
two independent guards refuse a decision naming a non-result manifest, and
removing either alone leaves the other covering the case. A case covered by
two guards is not covered twice as well — it is a case whose mutation must
remove both, and reporting it as a witness for either guard alone would be
false.

## Independent intake/cleanup sign-off — 2026-08-23 (baton.codex)

**Signed off for intake/cleanup through plan item 3w.** Both P1 findings are
closed: an existing decision reaches replay/collision before current output
indexing, while a new decision still requires sealed material; and every
loaded intake row is authenticated by its committed signature and typed,
digest-keyed result manifest. Missing journal evidence and digest substitution
fail closed with the correct integrity meaning.

One wording clarification explicitly supersedes the stronger sentence in the
second-correction entry above: writer and reader do **not literally construct
the operand record in one function**. The writer constructs it in
`recordIntake`; `intakeRecord` performs the reader-side canonical reassembly.
The invariant actually implemented is that both feed the same signature
formula and divergence fails closed. A new reviewer regression changes every
mutable decision operand independently and proves that invariant for the
current record.

Focused gate 30/30; full v12 gate 429/429. No behavioral finding remains in
this bounded slice. Item 4, a future pinned discard policy, the no-frozen-result
quarantine manifest and W2930 artifact-byte verification remain outside the
sign-off. Review and evidence: `review-2026-08-23T01-55-36Z.md` and
`evidence/signoff-intake-cleanup-2026-08-23.txt`.

## Item 4, first slice: certifying one agent-session profile — 2026-08-23

**A CLAIM THAT IS ONLY TRUE OF THE FORMULA IS ONE AN EDIT CAN QUIETLY
FALSIFY.** The intake sign-off recorded that "writer and reader build the
record in one place" was not literal. Weakening the sentence would have been
the cheap answer; the writer goes through the reader's builder now, so adding
a column changes both sides or neither.

**SHAPE, THEN SEAL, THEN POLICY — AND THE ORDER IS THE CONTENT.** Every later
rule reads members the schema has to establish; a policy decision about a
document whose bytes do not match its own digest is a decision about something
nobody agreed to. A document that breaks all three reports the shape failure,
and one that breaks the last two reports the seal.

**A RULE IS NEEDED WHERE THE SCHEMA CANNOT STATE IT — AND WHERE IT CAN, THE
SCHEMA IS THE GUARD.** The cross-posture policy rule decides for ACP, whose
branch pins both postures to one definition with a free-form `session_mode_id`
the schema cannot compare. For codex the schema already pins two different
definitions, so equal policies are unrepresentable and the shape check
answers. Asserting my rule decided both would have been a claim about my code
that the schema was quietly satisfying.

**CERTIFICATION IS BY DIGEST.** "The profile we agreed on" is a byte identity;
a manager that certified by name would let a later edit to a file of the same
name recertify itself, and the superseded bytes must stop being certified the
moment new ones are.

### Recorded

The suite's fixtures are the ACP boundary model's own profiles, `document_digest`
included, and both seals recompute exactly under this manager's
canonicalization — measured before the suite was written. Two independently
written boundaries arriving at the same seal is worth more than a fixture this
suite produced and then agreed with.

## Independent review of item 4 first slice — 2026-08-23 (baton.codex)

**Changes requested.** The composing `certifyAgentSessionProfile` path itself
performs shape, seal and policy in the recorded order, and the placed schema is
byte-identical to the frozen asset. Two other public paths defeat the boundary:

1. the older exported generic `certifyProfile` accepts `kind: "agent-session"`
   and writes an arbitrary digest without shape, seal, policy or secret checks,
   so the promised one certification route is not one; and
2. `issueOffer` looks up a certified digest without requiring `kind =
   'runtime'`, so a genuinely certified agent-session profile satisfies the
   separate runtime-profile offer axis.

Reviewer regressions reproduce both as the only two failures: focused 10/12,
full v12 439/441. A third additive regression pins frozen/product schema byte
identity and passes; the inverse kind check (runtime cannot satisfy the new
agent-session query) also passes. Review and evidence:
`review-2026-08-23T02-12-31Z.md` and
`evidence/review-agent-profile-slice-2026-08-23.txt`.

## The agent-profile slice, corrected — 2026-08-23

**A NEW DOOR DOES NOT CLOSE THE OLD ONE.** Both findings are that mistake. The
composing entry point performs shape, seal, posture policy and the secret
scan — and the pre-existing generic writer accepted `kind: "agent-session"`
and wrote a caller-authored digest into the same table, so every one of those
checks was avoidable by not calling the function that performs them. An entry
point a caller may decline to call is a suggestion.

**"CERTIFIED" WITHOUT A KIND IS A QUESTION WITH NO SINGLE ANSWER.**
Agent-session and runtime profiles are separate contract axes with separate
schemas, seals and policies. An unscoped lookup let a genuinely certified
agent-session profile satisfy an offer's runtime check — genuine bytes on the
wrong axis, which is harder to notice than a forgery.

**AN OPERAND THAT LOOKS AUTHORITATIVE AND IS NOT IS WORSE THAN NO OPERAND.**
The writer takes no `kind` and refuses one rather than dropping it, because
dropping a supplied `agent-session` would have written that digest as a
certified RUNTIME profile — an attempted forgery on one axis quietly
succeeding on another.

### Recorded

One mutation closes the cross-axis hole in the other direction — certifying
everything as `agent-session` — and immediately breaks the axis it was meant
to protect. Closing a hole is not the same as keeping the thing the hole was
in, so a case drives a runtime profile certifying a runtime offer, and another
drives a withdrawn one certifying nothing.

## Independent agent-profile correction sign-off — 2026-08-23 (baton.codex)

**Signed off for item 4's profile-certification first slice.** Both P1s are
closed: only the composing agent-session entry can create that profile kind,
and the runtime offer consumer now requires a runtime-kind certification.
Supplying a kind to the fixed runtime writer is deliberately refused and
writes no row; this is accepted as the fail-closed interpretation because
silently ignoring `agent-session` would certify the digest on an axis the
caller did not name.

The inverse kind check, both positive axis cases, runtime withdrawal and the
frozen/product schema byte-identity guard all pass. Focused gate 14/14; full
v12 gate 443/443. No finding remains in this bounded slice. Sessions, turns,
normalized events and adapter contracts remain unimplemented. Review and
evidence: `review-2026-08-23T02-22-39Z.md` and
`evidence/signoff-agent-profile-2026-08-23.txt`.

## Item 4, second slice: opening an agent session — 2026-08-23

**A DIGEST IS NOT A RECORD — APPLIED BEFORE IT WAS FOUND AGAIN.**
Certification held a digest and no document, and a session must pin the
per-posture policy that document carries. The bytes are retained, and the
loader re-validates and re-binds them to their key, because a guard on the way
IN cannot see an edit made afterwards.

**A RULE RESTATED IN TWO PLACES IS A RULE THAT CAN DISAGREE WITH ITSELF.** The
schema already pins consent's workspace and declared output to false and
execution's to true, so opening a session READS those bindings from the
certified profile. What is added here is only what the schema cannot state —
its own description names it: an execution session's assignment belongs to the
session's Work.

**A FRESH EPOCH IS A DERIVATION, NOT A PROMISE.** The manager never resumes,
forks or promotes a session, so the next epoch is computed as the next one and
there is no path that reuses one. Consent and execution count separately
because they never share a connection either.

**NO BATON CAPABILITY, BY CONSTRUCTION.** The boundary is given no session, no
token and no authority handle, so there is nothing to hand a provider. The
same move as intake taking no session — a rule kept by the shape of the
boundary rather than by the discipline of whoever edits it next.

### Recorded

One mutation was arithmetically identical to the code it replaced and passed
for that reason. A mutation that computes the same number is not a mutation.

And one case of mine was too blunt: it forbade the substring `authority` and
failed on `authority_uuid`, a Work reference column that is not a capability.
A guard that refuses legitimate names is not a stricter guard, it is a broken
one.

## Independent review of agent-session opening — 2026-08-23 (baton.codex)

**Changes requested.** Three P1 boundaries remain in item 4's second slice.

1. The retained-profile loader compares recomputed bytes with the row key but
   ignores the document's own declared digest, so a body with a false but
   well-formed `document_digest` opens a session.
2. Session opening unconditionally allocates `MAX(epoch) + 1`, permitting
   several concurrent nonterminal sessions for one posture despite the frozen
   `runtime-observation.duplicate-runtime` rule. The guard and allocator are
   not atomic across manager connections.
3. Execution opening trusts the attempt's cached assignment. A real authority
   assignment can end and the stale row still opens a writable execution
   session. The manager's participant-bound authority session must perform the
   liveness check; keeping that capability away from the provider/relay is a
   separate boundary.

Focused gate 10/13; full v12 gate 453/456, with the three additive reviewer
regressions as the only failures. Review and evidence:
`review-2026-08-23T02-36-51Z.md` and
`evidence/review-agent-session-slice-2026-08-23.txt`.

## The agent-session slice, corrected — 2026-08-23

**A STRUCTURAL TEST CAN ENCODE A MISUNDERSTANDING AS FIRMLY AS A RULE.** I
asserted "no Baton capability" of the function signature and called it keeping
the rule by construction. It conflated the trusted Worker Manager — which IS
the one Baton authority client and must reproject the assignment — with the
untrusted agent endpoint and relay, which are what must never receive a
capability. The test did not merely miss the liveness check; it defended its
absence. The rule now lives where it belongs: the handle is used for exactly
one read and appears in nothing returned and no durable column, and a case
asserts it WAS used, because a reprojection that never happened would satisfy
an absence test perfectly.

**FRESHNESS AND CONCURRENCY ARE TWO RULES.** Allocating the next epoch answers
only the first, and my freshness case opened three simultaneous sessions and
called that evidence. A partial unique index decides concurrency, because a
read of MAX followed by a separate insert is not an atomic allocator across
two manager connections — and only closing frees a posture. `unknown` does
not: transport ambiguity is where a second session is most tempting and least
safe.

**TWO OF THREE WITNESSES AGREEING IS NOT AGREEMENT.** A retained document's
declared seal, its recomputed canonical digest and the key it is filed under
are one fact, and comparing two of them left the third free to disagree.

### Recorded

The handle case's forbidden-substring list rejected `participant`, the
assignment's own identity — the same too-blunt guard recorded one round
earlier after `authority` matched `authority_uuid`. Twice is a habit, so the
warning now sits in the case rather than only in an evidence file.

## Independent re-review of corrected agent-session opening — 2026-08-23 (baton.codex)

**Changes requested.** The three prior P1s are closed: retained profile
loading binds declared, recomputed and keyed digests; a partial unique index
allows only one non-closed session per posture and only `closed` frees it; and
execution reprojects and compares the full live assignment before inserting.

One P1 remains at the participant boundary. `assignmentOf` projects a Work's
live assignment independent of the participant whose `V12Session` performs
the read. `openAgentSession` compares that projection with the cached
assignment but never compares the authority session's own participant with
the assignment participant. A genuine `poc.gemini` session therefore opens
and durably records an execution session assigned to `poc.claude`.

Snapshot and compare the manager authority session's participant binding with
the fixed assignment participant before opening execution. Retain the
real-authority, two-session reviewer regression. Focused gate 15/16; full v12
gate 458/459, with that regression as the only failure. Review and evidence:
`review-2026-08-23T02-51-57Z.md` and
`evidence/re-review-agent-session-correction-2026-08-23.txt`.

## The agent-session slice, second correction — 2026-08-23

**A PROJECTION IS SCOPED TO WHAT IT PROJECTS, NOT TO WHO ASKED.**
`assignmentOf` is Work-scoped, so a session minted for another participant
returns the same live assignment — and comparing all four assignment members
then proves the projection and the attempt agree while proving nothing about
the caller. The handle's own binding is a separate fact and is now compared
before anything is written.

**I HAD ALREADY WRITTEN THIS DOWN, IN THE MODULE NEXT DOOR.** The activation
slice's comment says it in one line: the claim says which assignment this
attempt won, the binding says who is asking. Re-deriving one of two rules and
not the other is how a lesson recorded in one place fails to reach the next —
which this Work has now seen with replay ordering, with sentinels, and here.

**A HANDLE IS NOT REQUIRED WHERE THERE IS NOTHING TO BIND TO.** A consent
session exists before any claim, so demanding an authority handle for it would
be demanding proof of something that does not exist yet.

### Recorded

Reading the binding into a local and calling it a snapshot claims more than it
does: measured, it is EQUIVALENT to reading the getter inline, because the
value is used exactly once and the stored participant comes from the attempt.
The local is kept so the single read stays visible, and the comment says that
rather than implying a guard.

## Independent sign-off of agent-session opening — 2026-08-23 (baton.codex)

**Signed off for item 4's agent-session opening slice.** The final
participant-binding P1 is closed: execution compares the authority session's
own participant with the attempt's fixed assignment participant before the
live projection or insert. A genuinely minted foreign authority session and
a missing binding both refuse without a durable session row; consent remains
handle-free because it precedes assignment.

All earlier corrections remain green: the three profile-digest witnesses
agree, one non-closed session per posture is enforced across connections,
only closure frees the posture, and an ended or changed live assignment opens
nothing. Focused gate 18/18; full v12 gate 461/461. No finding remains in this
bounded opening slice. Turns and deadlines, normalized events, adapter
contracts, and re-identification after ambiguity remain open. Review and
evidence: `review-2026-08-23T03-01-41Z.md` and
`evidence/signoff-agent-session-opening-2026-08-23.txt`.

## Item 4, third slice: the turn and its outcome — 2026-08-23

**THE ALTERNATIVE TO REFUSING IS GUESSING.** A turn that ended with no
terminal fact, no policy failure, no transport death and before its deadline
is a turn nobody can name an outcome for. Silence, transport closure, an empty
update stream, a tool call's own status and agent prose are each a guess
somebody could defend, so the selector refuses rather than picking one.

**AN ORDERING THAT IS ONLY A COMMENT IS NOT AN ORDERING.** A §4 violation ends
the turn where it happens and outranks anything arriving afterwards; a
terminal provider fact outranks an elapsed deadline because it ARRIVED; and
transport death outranks the deadline because the epoch is gone, which is more
than nothing having come back yet. Two mutations keep every individual mapping
and only reorder these, and both fail.

**A CLOSED VOCABULARY TESTED AT THREE OF EIGHT POINTS IS ONE NOBODY HAS
CHECKED.** The acceptance table is transcribed verbatim and driven for every
row, in both directions, with the two tables also checked against the
vocabulary and against each other — so an outcome with no gate, or no
conclusiveness, is caught rather than defaulted.

**THE GATE THAT WAS APPLIED, NOT ONE RE-DERIVED LATER.** The permitted set is
stored beside the turn. A reader that recomputed it would be reading today's
table about yesterday's decision.

### Recorded

`timeout` and `transport-lost` permit no disposition and are not conclusive,
and those are the same fact said twice: they are the outcomes that say the
relay does not know. Accepting a disposition on either would be the inference
the contract forbids, arriving through the gate instead of through the
selector.

## Independent review of the turn/outcome slice — 2026-08-23 (baton.codex)

**Changes requested.** The eight-value vocabulary, ACP mapping, precedence,
disposition gate, manager-deadline presence and session membership are
correct. Five P1 boundaries remain.

1. The Codex mapping contradicts the frozen provider table: terminal status
   `failed` is rejected instead of mapping to `agent-failed`, and every
   `codex-error-info` maps to `agent-failed` even though
   `ContextWindowExceeded` maps to `truncated` while the remaining certified
   values map to `agent-failed`. Unknown values are also accepted.
2. `recordTurn` bypasses the frozen turn-record shape and seal. Nonempty but
   invalid timestamps and a non-digest prompt are written successfully; the
   input surface cannot form the complete required turn document.
3. A policy failure selects `policy-failed` by array length and is then
   discarded. The durable turn retains neither the exact failure nor the
   full required record that would carry it.
4. Recording is not a journalled manager act. An exact retry surfaces a raw
   UNIQUE constraint, while changed operands under the same identity are not
   translated to the closed operation-collision refusal.
5. The first answer returns the caller's `terminalFact` object directly, so a
   later caller mutation rewrites the already-returned answer, contrary to the
   dossier's no-alias boundary.

Six additive regressions are the only failures: focused 13/19; full v12
474/480. Review and evidence: `review-2026-08-23T03-15-42Z.md` and
`evidence/review-agent-turn-slice-2026-08-23.txt`.

## The turn slice, corrected — 2026-08-23

**A VOCABULARY I SHORTENED IS NOT A STRICTER VOCABULARY.** The frozen boundary
maps three Codex terminal statuses; I carried two and wrote a case asserting
the third must be refused. It is a different vocabulary, not a safer one, and
the difference was invisible because the same hand wrote the code and the test
that defended it — the second time in three rounds that one of my cases has
protected a misreading rather than caught it.

**SAMPLING A TABLE LEAVES IT LOOKING DRIVEN.** §10.6 has eleven rows, each
carrying an outcome AND the closed error pair it is reported as. Three of them
tested is eight untested, so every row is driven and the pairs are compared —
the transport rows against the provider rows, because that difference is why
the table carries a pair at all.

**FOUR FINDINGS, ONE CORRECTION.** Shape and seal bypassed, the deciding
policy fact discarded, the act neither replay- nor collision-safe, and the
first answer aliasing the caller. All four are the same absence: the record was
never built as the frozen document it claims to be. Building it, validating it
before reading semantic members, sealing it and committing it through the
operation journal answers all four at once — and the journal's byte-stable
result is what makes the answer owned.

**A DISAGREEMENT BELONGS IN THE HANDOFF, NOT IN THE CODE.** The review asks an
unrecognized `codexErrorInfo` to refuse; §10.6 says it takes the last row. The
frozen sentence is implemented and the quote sits beside it, because diverging
silently in the stricter direction is still diverging.

### Recorded

Two mutations are measured rather than counted. The per-failure policy
validation is MASKED by the record-level one and is kept only for naming which
failure. And copying the caller's terminal fact is EQUIVALENT, because
`store.transact` already returns the bytes it committed — the journal owns the
answer, and a comment claiming the clone does would be crediting the wrong
line.

## Independent re-review of corrected turn/outcome — 2026-08-23 (baton.codex)

**Correction to the prior review.** The prior claim that unknown
`codexErrorInfo` must refuse is superseded. Frozen §10.6 explicitly says an
unrecognized value takes the last row, so the corrected implementation's
`agent-failed` / `unavailable.source-provider` answer is right.

**Changes requested.** The prior five P1s are otherwise closed, but two P1
durable boundaries remain. First, the complete turn body never passes through
the durable-secret guard. A live bearer nested under adapter diagnostics is
written to `turns.body`; the journal sees only a clean summary that omits that
member. Second, `permitsDisposition` bypasses the canonical sealed record and
trusts the independent `turns.permitted` summary. Editing that summary makes a
refused turn permit `completed` while its sealed body still forbids it.

Guard the exact complete document before persistence. On read, validate and
bind the frozen record's shape, declared/recomputed/stored digest and requested
turn identity, then make every safety decision consume or cross-check that
authenticated record. Focused gate 26/28; full v12 gate 487/489, with the two
additive regressions as the only failures. Review and evidence:
`review-2026-08-23T03-32-55Z.md` and
`evidence/re-review-agent-turn-correction-2026-08-23.txt`.

## The turn slice, second correction — 2026-08-23

**A SCAN OVER A PROJECTION IS A SCAN OVER THE PROJECTION.** The operation
journal applies the durable-secret boundary to the result it commits, and that
result was a summary omitting `evidence` and `adapter_diagnostics` — so a live
bearer under an innocently named diagnostic reached `turns.body` while the
journal reported no leak. A guard covers what it is given, and reasoning that
an existing guard "already covers this" is a claim about what it is given.

**A SEAL THE CONSUMER DOES NOT CONSULT PROTECTS NOBODY.** The canonical sealed
record existed and the one safety decision still read an unsealed summary
column. The gate consumes the record now, and the summary must agree with it:
a drifted query column is an integrity failure wherever it is found, not
something to quietly prefer the sealed side of, because the next reader may be
one that only has the column.

**THREE DIGESTS CAN AGREE WHILE THE RECORD ANSWERS TO SOMEBODY ELSE.** The
declared, recomputed and stored digests bind a document to itself; the
identity the caller ASKED FOR is a fourth witness, and copying one row's body
and seal onto another satisfies the first three exactly.

**BEING STRICTER THAN A FROZEN CONTRACT IS STILL DISAGREEING WITH IT.** The
re-review resolved the §10.6 point in the implementation's favour. What made
that resolvable was raising it on the handoff with the quote rather than
diverging silently — and the divergence being asked for was the stricter one,
which is the kind that looks safe enough not to mention.

### Recorded

Two mutations are measured rather than counted: the gate's read of the sealed
record is MASKED by the summary comparison that precedes it, and the shape
check on the read path is INERT given the write-side validation and the seal.
Both are kept, and neither is presented as a guard it is not.
