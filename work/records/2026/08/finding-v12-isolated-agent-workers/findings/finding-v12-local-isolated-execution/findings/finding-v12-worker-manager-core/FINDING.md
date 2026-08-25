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

## Independent third re-review of corrected turn/outcome — 2026-08-23 (baton.codex)

**Accepted:** both P1s from the preceding re-review are closed on their
reported paths. The complete owned turn document is scanned before a new
write, and the disposition gate authenticates the sealed record, requested
identity and query summary.

**Observed — changes requested:** four adjacent boundaries remain. A turn id
derived only from session epoch and prompt digest conflates distinct
same-content supervised turns. Session admission checks only that a row
exists, allowing a new turn after `closed` and allowing the caller's provider
session id to disagree with the durable session record. Current secret
liveness is checked before journal replay, so registering previously benign
durable text as a bearer hides an exact committed answer. Finally, malformed
`policyFailures` and malformed retained summary JSON escape as raw
`TypeError`/`SyntaxError` rather than closed contract pairs.

Six additive regressions reproduce the boundaries as the only failures:
full v12 gate 492 passed and 6 failed out of 498. Exact findings and evidence
are in `review-2026-08-23T14-47-38Z.md` and
`evidence/review-agent-turn-round3-2026-08-23.txt`.

## The turn slice, third correction — 2026-08-23

**EQUAL BYTES ARE NOT THE SAME ACT.** The turn identity was derived from the
session epoch and the prompt digest, so two supervised turns that happened to
send the same prompt were one operation. The separating component has to be
MANAGER-OWNED and free of prompt content, and §5.1 already names one: every
turn carries a manager deadline, so `(started_at, deadline_at)` is the
supervision window the manager allocated for THIS turn. `ended_at` stays out
of it, because that is what the manager later OBSERVED — folding an
observation into an identity would mint a second turn document for a retry
that merely reported a different end, and a changed end under one window
should collide.

**THE WINDOW IS A COMPONENT, NOT A UNIQUENESS RULE.** Two turns may
legitimately share a window and differ by prompt, and an accepted case already
does. Refusing that would have been inventing a serialization §5 does not
state, so the component carries no uniqueness rule of its own and the prompt
digest still separates that pair.

**A ROW EXISTING IS NOT THE SESSION IT NAMES.** Admission selected `state` and
then used the row only for presence, so a `closed` epoch sealed a new turn and
a caller could name one provider session while the durable row named another.
§3.3 makes `closed` and `unknown` terminal and §3.1 says the reference LABELS
EVIDENCE — a label that disagrees with the record it labels is worse than
none. The admitting states are now a closed set named POSITIVELY, because a
list of the states where a turn may NOT settle is a list a newly frozen state
joins silently and wrongly.

**AN IMMUTABLE ANSWER IS RESOLVED BEFORE TODAY'S STATE.** Both the durable-
secret liveness scan and that admission ran before the operation journal could
answer, and both read state that MOVES. Ordinary durable text that was benign
when committed could later be registered as an ephemeral bearer and start
refusing an exact replay — writing nothing, returning no bearer-bearing field,
and hiding an immutable answer whose bytes had not changed; a session closing
after a turn legitimately settled could do the same. Moving both inside the
journalled transaction answers both, and a genuinely new write still refuses.

**AN INTERPRETER-AUTHORED ERROR IS NOT A CLOSED PAIR, HOWEVER ACCURATE.**
`policyFailures: null` left as a raw `TypeError` and a non-JSON retained
summary as a raw `SyntaxError`. The collection shape is proved before anything
iterates it, and a summary that cannot even be COMPARED with the sealed record
has already diverged from it — which is the same integrity failure a
comparable-but-different summary reports.

### Recorded

**One deliberate strictness beyond the review, raised rather than buried.**
The review asked only that a terminal or ambiguous epoch admit no new turn;
`not-started` and `initializing` are refused too, because no prompt has been
issued in either. Nothing in this slice moves a session out of `not-started`
yet, so the state transitions a later slice adds must reach an admitting state
before recording a turn. The partition is driven exhaustively against the
frozen `sessionState` enum read from the placed schema, in both directions.

One mutation is measured rather than counted: `turnSessionRef` is **masked**
by the frozen record validation, which refuses the same malformed references
with the same pair. It is kept because the reference now reaches the identity
digest and the durable body before any row is read, and its case asserts the
behaviour rather than the line.

## Independent fourth re-review of corrected turn/outcome — 2026-08-23 (baton.codex)

**Accepted:** the session-reference/state admission, immutable-answer ordering,
null collection handling, malformed summary handling, and all six preceding
review regressions are closed on their reported paths.

**Observed — changes requested:** the supervision window is not allocated,
recorded, made unique, or atomically bound as one manager-owned identity per
turn; it remains reusable caller-supplied data and `promptDigest` still decides
whether reuse means one act or two. This does not close the prior P1's explicit
allocate-or-validate requirement. Two adjacent malformed shapes also escape
the closed taxonomy: a non-cloneable policy-failure element throws raw
`DataCloneError`, and unparsable retained turn-record bytes throw raw
`SyntaxError`.

Two additive regressions are the only test failures: full v12 gate 504 passed
and 2 failed out of 506. Exact findings and evidence are in
`review-2026-08-23T15-09-47Z.md` and
`evidence/review-agent-turn-round4-2026-08-23.txt`.

## Independent fourth re-review of corrected turn/outcome — 2026-08-23 (baton.codex)

**Accepted:** full session admission, replay-before-mutable-state ordering,
the `policyFailures: null` and malformed-summary closed pairs, and all six
third-review regressions.

**Observed — changes requested.** The supervision window is reusable data,
not a per-turn identity. Nothing allocates it, records that allocation, or
enforces uniqueness within the epoch, and `prompt_digest` remains the value
that decides whether a reused window means one act or two. Two additive
regressions expose a raw `DataCloneError` for a non-cloneable policy-failure
element and a raw `SyntaxError` for unparsable retained record bytes. Full
v12 gate 504 passed, 2 failed, 506 total. Review and evidence:
`review-2026-08-23T15-09-47Z.md` and
`evidence/review-agent-turn-round4-2026-08-23.txt`.

## The turn slice, fourth correction — 2026-08-23

**AN IDENTITY IS ALLOCATED; OPERANDS THAT HAPPEN TO DIFFER ARE NOT ONE.** Asked
for one manager-owned identity per supervised turn, allocated or validated
atomically within the epoch, I supplied a digest of the caller's `started_at`
and `deadline_at` and kept `prompt_digest` to tell two reuses apart. Every
word of the finding still applied to the answer: nothing allocated it, nothing
recorded the allocation, no constraint bounded it, and prompt bytes were still
the fallback. Restating a requirement in different data is not meeting it.

**THE SUPERVISION BOUNDARY IS WHERE AN IDENTITY BELONGS.** §5.1 already says
the manager opens a turn and gives it a deadline before issuing the prompt, so
that is the moment at which a turn identity can exist without deriving from
anything the agent said. Schema 12's `turn_allocations` claims a per-epoch
ordinal, the UNIQUE constraint makes epoch-local uniqueness a fact rather than
an intention, and the turn record REFERENCES the allocation it was written
under. The identity carries an attempt, a posture, an epoch and an ordinal —
nothing else.

**PROMPT BYTES BELONG IN THE SIGNATURE, WHICH IS WHERE THEY DECIDE THE RIGHT
QUESTION.** Under one allocated turn a changed prompt is changed operands for
one act and collides. It cannot become a second turn, which is what it silently
did while the identity was carrying it. The deliberate exclusion of the
observed `ended_at` is now structural rather than argued: no operand reaches
the identity at all.

**ALLOCATION IS NOT JOURNALLED, AND THAT IS THE POINT.** An operation journal
replays an act by its identity; allocating is how an identity comes to exist,
so keying it under an invented id would invent the thing allocation produces.
A retried allocation mints a fresh ordinal and the abandoned one is a GAP —
visible, harmless, and honest about a turn the relay opened and did not finish.
What must survive a retry is the RECORD, and it does, because the relay holds
the token it was given.

**OPENING A TURN AND SETTLING ONE ASK DIFFERENT QUESTIONS.** Allocation checks
that the epoch exists; whether a turn may still SETTLE there is decided at the
moment it settles, against the state that holds then. This also keeps every
record-time boundary the third review installed genuinely exercised at the
record call rather than pre-empted at allocation.

### Recorded

**Two existing assertions were changed because the ruling superseded them, and
both are named rather than absorbed.** `"the turn identity is derived from its
epoch and prompt"` asserted that the prompt was part of the identity — exactly
what this review ruled out — and `"the manager's supervision window identifies
the turn"` was the third correction's own case for the superseded design. Two
further fixtures had their SETUP revalidated with assertions untouched: the
same-window/different-prompt case the review named, and the four-outcome case
that told four turns apart by prompt bytes. Each is now two, or four,
allocations.

Two mutations are measured rather than counted. The turn-token shape proof is
**masked** — measured, not assumed: without it `undefined` refuses in
`canonicalBytes` and the rest refuse in the frozen record validation on
`/turn_id`, with the same closed pair and a worse message. The
`turns -> turn_allocations` foreign key is **masked** by the binding that
refuses an unallocated or foreign token first; both are kept, because a key
says a record belongs to an allocation and the binding says WHICH epoch. And
the two clone guards MUTUALLY mask: either alone refuses the reviewer's
element, and both must go for the case to fail.

## Independent fifth re-review of corrected turn allocation — 2026-08-23 (baton.codex)

**Accepted:** schema 12 now durably allocates a database-constrained ordinal
per epoch; the turn token excludes prompt and observation operands; prompt
bytes moved to the effective signature; turn records bind their allocations;
and both fourth-review malformed-shape regressions report closed pairs. The
delivered gate is 508/508.

**Observed — changes requested:** `allocateTurn` defines the boundary that
opens a supervised turn before the external prompt, but admits any existing
epoch and ignores its durable provider-session id. It therefore allocates in
all terminal and pre-prompt states and returns a mismatched evidence label.
Frozen §7.3 permits prompt start only at `ready -> prompting`; §3.3 makes
`unknown` and `closed` terminal and defines `closed` as terminal facts for
EVERY turn the epoch started; §3.1 requires the full reference to label the
evidence it actually belongs to. Record-time settlement admission cannot
protect a prompt that allocation already authorized.

One additive regression drives the complete non-`ready` state set and the
provider mismatch, requires no allocation on refusal, then accepts the exact
ready reference at ordinal one. It is the only failure: full v12 gate 508
passed and 1 failed out of 509. Exact finding and evidence are in
`review-2026-08-23T16-15-49Z.md` and
`evidence/review-agent-turn-round5-2026-08-23.txt`.

## Independent fifth re-review of corrected turn allocation — 2026-08-23 (baton.codex)

**Accepted:** the schema-12 allocation, the token identity, the
prompt/signature separation, and both round-4 closed-error corrections.

**Observed — changes requested.** `allocateTurn` is the supervision boundary
and admits only that the epoch exists, so it durably opens a turn in every
non-`ready` state including the terminal ones and accepts a mismatched
provider-session label. §7.3 permits a prompt to start only on
`ready -> prompting`; §3.3's `closed` asserts a terminal fact for every turn
the epoch started. Deferring both checks to `recordTurn` is too late, because
allocation precedes the external prompt. One additive regression; delivered
gate 508/508, reviewed gate 508/509. Review and evidence:
`review-2026-08-23T16-15-49Z.md` and
`evidence/review-agent-turn-round5-2026-08-23.txt`.

## The turn slice, fifth correction — 2026-08-23

**OPENING ASKS THE STRICTER QUESTION, NOT A WEAKER ONE.** The round-4 record
says allocation deliberately skips the state and provider checks because
"opening a turn asks whether the epoch exists; whether a turn may still SETTLE
there is a question about the moment it settles". **That reasoning is
superseded.** The distinction between opening and settling is real and both
boundaries are kept, but the conclusion drawn from it was backwards. §7.3
draws exactly one edge that starts a prompt, `ready -> prompting`, so every
other state is either before a prompt is possible or past one; §3.3's `closed`
asserts a terminal fact for every turn the epoch started, so an allocation
landing afterwards does not leave a harmless gap — it makes a durable session
assertion false the instant it commits. A turn OPENS only from `ready` and may
SETTLE wherever the graph has legally advanced to since.

**A CHECK DEFERRED PAST THE THING IT PROTECTS IS NOT A DEFERRED CHECK.**
Allocation precedes the external prompt; recording follows the terminal fact.
Whatever the opening boundary is for, asking it at recording time asks it after
the prompt has already gone out.

**AND THE SECOND HALF OF THAT ARGUMENT WAS ABOUT FIXTURES.** Round 4 also
justified the omission by saying a start-time check would pre-empt the
record-time boundaries the third review installed, so several cases would pass
for the wrong reason. That is a true statement about the tests presented as a
statement about the design — the same shape as round 4's window defence, one
round later. The tests needed migrating, and the review said how: open while
`ready`, then move the state, which is what a relay does.

### Recorded

Two of the reviewer's own round-3 cases are now decided at the START boundary
rather than the settle one, with their assertions untouched. That is named
rather than glossed, and the settle-side coverage it displaces is carried by
the two migrated cases — mutations disabling the settle state check and the
settle provider binding each still fail a different case, so both boundaries
remain independently witnessed.

`TURN_STARTING_SESSION_STATES` and `TURN_ADMITTING_SESSION_STATES` are held
apart by a property rather than by habit: START is exactly `ready`, START is a
strict subset of SETTLE, the two cannot collapse, and both are drawn from the
frozen vocabulary.

## Independent sign-off of the fifth turn correction — 2026-08-23 (baton.codex)

**Signed off for plan item 4n.** Allocation now admits exactly the durable
`ready` session and its full provider identity under the same write lock and
before inserting, so every refused start leaves no allocation. Settlement
keeps its broader positive state set and independently rechecks the provider
binding after immutable replay. The migrated cases still witness both
settlement predicates instead of merely turning green at the new start gate.

The full v12 gate is 511/511 and `git diff --check` is clean. This is bounded:
adapter prompt composition, event normalization and transport-ambiguity
re-identification remain open. Review and evidence:
`review-2026-08-23T16-28-19Z.md` and
`evidence/signoff-agent-turn-round5-2026-08-23.txt`.

## The event-normalization slice — 2026-08-23

**COUNTED, NEVER GUESSED AT.** §6.1's `other` is an escape hatch with teeth.
An update kind this contract has never seen becomes `other`, keeps the
provider's own string verbatim as diagnostics, and carries no portable content
— while its bytes are still counted. A relay that guessed would be inventing
agent evidence; one that dropped would report a partial stream as a complete
one, and those are the only two alternatives.

**`other` CARRYING NO CONTENT IS A RULE, NOT A DESCRIPTION.**
`user_message_chunk` maps to `other` and arrives WITH content, because the
relay authored that prompt and an echo of it is the transport talking back. A
normalizer that passed content through whenever it happened to be present
would quietly turn the relay's own prompt into durable agent evidence.

**THE BYTES DO NOT COME IN.** §6.3 admits `text` and `resource_link`. Image,
audio and embedded resource blocks are recorded as their type and byte count
with the bytes gone, and a block type this contract has never seen becomes
`unknown` rather than being discarded — a dropped block that left no trace
would turn a partial record into an apparently complete one.

**THE SEAL COVERS THE FRAME, NOT THE OBSERVING OF IT.** `late` and the
manager's `observation_seq` are properties of an OBSERVATION and live in their
own columns. The reason is concrete and §6.4 states it: a retransmitted frame
is the same frame, so sealing lateness in would give one frame observed twice
— once before a turn ended and once after — two different digests, making an
ordinary duplicate indistinguishable from a spliced stream. Lateness is
decided when the frame is FIRST seen and a retransmission replays that
original observation.

**AND THE SEAL IS CHECKED BEFORE ANY OTHER FIELD.** A frame whose digest was
never verified has no claim on the identity, sequence or duplicate rules, so
authentication precedes all three rather than sitting among them.

### Recorded

**Two exclusions, named rather than left to be discovered.** §6.5's bounded
relay queue is a RELAY structure and belongs with the still-open adapter
contracts; the manager's durable half of it already exists as the turn
record's `dropped_event_count` and `dropped_event_bytes`. And this boundary
deliberately does NOT gate on session state: §6.4 gives it identity, sequence
and lateness rules and no state rule, so inventing one would be this module
deciding a question §7.3 owns. A case records that omission as a decision.

Schema 12 → 13 adds `agent_events`, keyed by `(attempt, posture, epoch,
source_seq)` — which is the duplicate rule stated at the database boundary —
with the manager's ordering unique within the epoch it orders.

## Independent first review of event normalization — 2026-08-23 (baton.codex)

**Accepted:** schema-13 event identity and ordering, the closed taxonomy,
ordinary content restriction, counted-and-dropped binary/resource blocks,
seal-before-identity admission, different-seal collision, first-observation
lateness, retained-read authentication and whole-document secret scanning.

**Observed — changes requested:** six additive regressions isolate four P1
boundaries. Reasoning content currently becomes portable evidence despite
§6.2; tool calls expect a nested object rather than the root-level ACP shape
in the frozen trace; observation returns no sealed document and replay never
authenticates the retained body; an omitted optional turn operand can discard
the sealed non-null `turn_id`; and the event limit trusts the document's
claimed `byte_count` instead of measuring its canonical bytes. Full v12 gate:
540 passed and 6 failed out of 546, with only the new reviewer cases failing.

The exact correction boundary, case-specific existing-test migrations and one
open prose/schema mismatch for ACP tool-call `kind` are recorded in
`review-2026-08-23T16-47-06Z.md`; evidence is
`evidence/review-event-normalization-round1-2026-08-23.txt`.

## Independent first review of event normalization — 2026-08-23 (baton.codex)

**Accepted:** the schema-13 ledger and its database-constrained duplicate
identity, lateness and observation sequence beside the sealed frame, the
closed ten kinds and thirteen mapping rows, counted-and-dropped blocks,
seal-before-identity, collision on differing seals, first-observation lateness
replay, retained re-binding and the durable secret scan.

**Observed — changes requested.** Four P1 boundaries. `agent_thought_chunk`
content became portable despite §6.2 marking reasoning "never portable
evidence". The tool-call path read a nested `toolCall` member while the frozen
captured trace carries `toolCallId` and `status` at the update ROOT.
`observeEvent` neither returned the sealed document nor authenticated the
retained body on replay. An omitted `turnId` option discarded a sealed
non-null `turn_id`. And the limit trusted the document's own `byte_count`
rather than canonical event bytes. Six additive regressions; gate 540/546.
Review and evidence: `review-2026-08-23T16-47-06Z.md` and
`evidence/review-event-normalization-round1-2026-08-23.txt`.

## The event slice, first correction — 2026-08-23

**A MAPPING TABLE IS HALF THE CONTRACT; THE CAPTURED TRACE IS THE OTHER HALF.**
I read §6.2's table and built the tool-call path against a shape ACP does not
send — `toolCallId` and `status` live at the update ROOT in the frozen trace —
and my own fixture agreed with my code because I wrote both. The same reading
failure produced the reasoning defect: §6.2 marks `agent_thought_chunk`
content "diagnostics; never portable evidence", which is the same sentence
about a different row, and I applied it to `other` alone.

**AN INDEX IS NOT A RECORD.** The replay path compared the indexed digest
column and returned metadata without reading the body, so a retained frame
that had become unreadable was reported as a successful replay. The one place
a stale index is most convincing is the place a record is never read.
`authenticateRetained` is now shared by the reader and the replay path, and
both answers carry the document §6.4 requires.

**AN AUTHENTICATED IDENTITY MEMBER CANNOT BE OPTIONAL.** A separate `turnId`
operand defaulted to null and was what got written, so a frame SEALED for a
turn became a durable unbound event whenever a caller omitted the option —
losing the identity and giving lateness the wrong subject. The sealed
`turn_id` is the identity; a redundant operand may only agree, in both
directions.

**A BOUND OVER A SELF-DESCRIBED SIZE IS NOT A BOUND.** `byte_count` is source
accounting living inside the untrusted document and may claim `1` while the
event is far over the limit. The bound now measures the canonical bytes of the
thing being bounded, and `byte_count` keeps its distinct job of saying how
much source there was, including the parts that were dropped.

### Recorded

**An open contract inconsistency, carried forward rather than resolved.**
§6.2's prose says `tool_call` carries the ACP `kind`; the frozen
`$defs.toolCallView` permits only `tool_call_id`, optional `title` and
`status` with `additionalProperties: false`. Two frozen artefacts disagree.
No portable `kind` member is invented in this slice, and a case asserts the
normalized view has exactly `tool_call_id` and `status` even when the update
carries `kind`. **This needs an owning record before any implementation relies
on that field.**

Three existing cases were migrated on the review's explicit case-specific
authority: two fixtures moved to the captured root-level tool-call shape with
every id and status assertion preserved, and one exact expected answer was
extended with the document §6.4 requires. One mutation is measured rather than
counted: the answer's clone is **equivalent**, because `authenticateEvent`
already reaches an owned object through a serialize/parse round-trip.

## Independent second review of corrected event normalization — 2026-08-23 (baton.codex)

**Accepted:** all four first-review P1 boundaries and all six regressions are
closed. The mapping corrections, durable-document answer/replay, sealed turn
identity and canonical event bound now match the frozen evidence on their
reported paths; the three authorized existing-case migrations preserve their
prior assertions.

**Observed — changes requested:** the adjacent retained reader accepts a full
session reference but ignores its provider-session component, so a request for
provider B returns an event sealed for provider A. Separately, `sealEvent`
clones unproved values directly and leaks raw `DataCloneError` for a
non-durable diagnostic instead of the closed `integrity.schema` pair. Two
additive regressions are the only failures: full v12 gate 550 passed and 2
failed out of 552. Exact review and evidence:
`review-2026-08-23T17-01-19Z.md` and
`evidence/re-review-event-normalization-round2-2026-08-23.txt`.

The carried-forward ACP tool-call `kind` prose/schema contradiction now has
its own durable owner, W543,
`work/records/2026/08/finding-acp-tool-call-kind-contract-conflict/`; it is
not silently resolved in this implementation slice.

## Independent second review of corrected event normalization — 2026-08-23 (baton.codex)

**Accepted:** all four preceding P1 boundaries and all six first-review
regressions, plus the three authorized fixture/expectation migrations.

**Observed — changes requested.** `eventRecordOf` accepts the full session
reference and selects on attempt, posture and epoch only, so a caller asking
for provider session B receives a frame sealed for provider session A — the
write path's identity mismatch reached through the read path. And `sealEvent`
clones caller content, tool-call data and diagnostics before the schema
boundary, so a non-cloneable member escapes as raw `DataCloneError` instead of
`integrity.schema`. Two additive regressions; gate 550/552. Review and
evidence: `review-2026-08-23T17-01-19Z.md` and
`evidence/re-review-event-normalization-round2-2026-08-23.txt`.

## The event slice, second correction — 2026-08-23

**BINDING THREE QUARTERS OF A REFERENCE IS NOT BINDING IT.** §3.1 makes the
provider session id part of the reference, and the write path already refused
a disagreement. The read path selected its row on the other three components
and then authenticated only the seal and the sequence, so the same mismatch
was reachable by asking instead of by writing. The requested reference is now
a fifth witness beside the shape, the declared digest, the recomputed digest
and the sequence.

**ABSENCE AND DISAGREEMENT ARE DIFFERENT ANSWERS.** A genuinely absent
`(attempt, posture, epoch, source_seq)` is null. A PRESENT row whose sealed
reference disagrees refuses — answering null there would tell a caller no such
frame exists while the epoch holds one, which is a worse lie than the one
being corrected.

**AN INTERPRETER EXCEPTION IS NOT A CLOSED PAIR.** The same rule the turn
slice learned twice, at a third boundary: `structuredClone` over caller
content, tool-call data and diagnostics leaked `DataCloneError`. All three go
through `ownDurable` now, and the seal is wrapped separately because
`canonicalBytes` is the other place a caller's value becomes durable.

**AND A PRECISE REFUSAL IS NOT IMPROVED BY WRAPPING IT.** An existing
`ContractError` passes through unchanged, because `canonicalBytes` names its
rules exactly — a non-finite number, a negative zero, a lone surrogate — and a
general "cannot own this" would report the same pair while telling the caller
less.

### Recorded

**Two mutation instruments were wrong on the first pass, and both were
silent.** One read `if (false && a || b || c || d)`, where `&&` binds tighter
than `||`, so it disabled only the first clause — which no case drives — and
reported zero witnesses that meant nothing. The other asserted only that the
precise text APPEARED in the message, which flattening satisfies by
interpolation. Both are fixed and both now fail. A mutation that reports zero
is a claim about the code; twice here it was a defect in the instrument, and
that is the same class of error as trusting a fixture one wrote oneself.

Two measurements: the retained-reference comparison is **inert** from the
replay path, because equal digests already mean equal references there, and
`ownDurable`'s ContractError pass-through is **unreachable**, because
`structuredClone` raises no `ContractError`. Both are kept — one function for
one rule, and symmetry with the seal wrapper where the same line is
load-bearing — and neither is counted as a guard.

**The carried-forward contract defect now has an owner.** The §6.2-prose
versus `toolCallView` disagreement over a tool-call `kind` member is W543 at
`work/records/2026/08/finding-acp-tool-call-kind-contract-conflict/`. This
slice continues to invent no such member; nothing here waits on W543 and W543
excuses nothing here.

## Independent sign-off of the second event correction — 2026-08-23 (baton.codex)

**Signed off for plan item 4q.** The retained reader now binds all four
components of the requested session reference after authenticating the body,
while preserving null for genuine absence. The seal boundary owns content,
tool-call data and diagnostics through a closed helper; the canonical seal is
wrapped separately; and precise existing `ContractError` evidence passes
through unchanged. The stronger cases distinguish reference mismatch from
digest failure and precise refusal from interpolated general text.

Focused event gate 44/44, full v12 gate 555/555, and `git diff --check` clean.
This is bounded: §6.5 relay queueing, adapter composition, runtime/agent
adapter contracts and transport-ambiguity re-identification remain open; W543
owns the independent ACP tool-call `kind` contract conflict. Review and
evidence: `review-2026-08-23T17-11-20Z.md` and
`evidence/signoff-event-normalization-round2-2026-08-23.txt`.

## Independent sign-off of the corrected event slice — 2026-08-23 (baton.codex)

**Signed off for plan item 4q.** The retained reader binds all four requested
session-reference components while preserving genuine absence, and the seal
boundary owns every caller-supplied durable member through the closed taxonomy
while preserving precise canonical `ContractError` evidence. Focused event
gate 44/44, full v12 555/555. Bounded: §6.5, adapter composition and
contracts, transport-ambiguity re-identification and W543 remain outside it.
Review and evidence: `review-2026-08-23T17-11-20Z.md` and
`evidence/signoff-event-normalization-round2-2026-08-23.txt`.

## The handshake slice — 2026-08-23

**THE SETS BELONG TO THE VERSION, NOT TO A PROFILE.** §2.3 says so and gives
the reason: a certified profile that disagrees with the policy actually
enforced is worse than no profile, because it is a second source of truth
wearing the first one's authority. The required, refused, client-method and
capability sets are module constants. A profile supplies which wire it speaks,
which version it pins and which build it was certified against — never which
methods are required.

**THE RELAY ADVERTISES NOTHING, AND THE COMPARISON IS EXACT.** §2.2 withholds
every client capability rather than everything unsafe. A subset check asks
whether what is present is safe; the rule is that nothing may be present, and
a member ACP adds next version would pass a subset check on the day it
appeared. `session` is stable, is not in the unstable set, and is still not
advertised — which is the difference between the two readings, so a case
asserts it.

**BINDING REPLACES NEGOTIATION; IT IS NOT A SECOND SPELLING OF IT.** A
provider that documents no protocol version has nothing to negotiate and
nothing to refuse a downgrade against, so certification binds an exact build
and its captured interface digest instead. Each door refuses the other's
profile, so neither is reachable by the wrong one.

**AND THE REFUSALS DO NOT DEPEND ON THE OFFER.** §2.3 refuses its list
"whether or not advertised", so an agent offering `session/resume` changes
nothing about whether this relay may call it. The advertisement is simply not
consulted, and a case drives exactly that.

### Recorded

**Written and tested against the frozen model, deliberately.** The first event
review caught a normalizer built from §6.2's prose while the captured trace
said otherwise, with a fixture that agreed because one author wrote both. The
constants here are transcribed from `evidence/acp_boundary_model.py` and the
case file PARSES that file and compares member for member rather than retyping
them.

One mutation is measured rather than counted: the experimental-API check is
**unreachable** for a certified profile, because the frozen schema makes
`experimental_api` a constant `false` and such a document cannot be certified
at all. The case drives the refusal at certification, where it actually lands.

**One mutation instrument was again at fault before it was believed.** The
wire-protocol mutation reported zero because the case offered a version the
profile did not pin, so the version rule refused it first with the same pair
for a different reason. Corrected to offer the pinned value, it fails. The
previous round recorded this class of error twice; checking for it is now part
of reading a zero.

## Independent first review of the handshake slice — 2026-08-23 (baton.codex)

**Changes requested for plan item 4s.** The version/profile binding, mandatory
method and capability checks, module-owned sets, and rejection of every
currently enumerated refused/client method are accepted. Two adjacent
boundaries remain open.

First, the implementation uses the durable snake-case capability summary as
ACP wire data, refusing §2.2's exact `{ "fs": {}, "terminal": false }` and
comparing JSON serialization rather than structure. W641 now owns the
pre-existing frozen-model/schema/spec conflict; W4 must distinguish wire data
from durable normalized evidence at the transport boundary.

Second, both method guards reject only names in today's negative lists and
default-allow everything else. The outbound version surface and the entirely
withheld client-call surface must instead fail closed, including
`session/reuse` and future methods, while the known agent-origin
`session/update` route remains distinct. Focused 14/18; full v12 569/573; only
the four additive review regressions fail. Review:
`review-2026-08-23T17-26-19Z.md`; evidence:
`evidence/review-handshake-round1-2026-08-23.txt`.

## Independent first review of the handshake slice — 2026-08-23 (baton.codex)

**Accepted:** exact version negotiation and provider build/interface binding
as separate doors that refuse each other's profiles, mandatory certification,
all five methods and all six capabilities, the version-owned module constants,
and the enumerated refusals with their closed error pairs.

**Observed — changes requested.** Two P1. `MINIMAL_CLIENT_CAPABILITIES` copied
the durable snake-case profile summary onto the ACP transport, so the boundary
refused §2.2's exact wire document and emitted field names ACP does not have;
the comparison was also serialization-order sensitive. And both claimed closed
method surfaces were DENY LISTS that returned every unenumerated name by
default. Four additive regressions; gate 569/573. Review and evidence:
`review-2026-08-23T17-26-19Z.md` and
`evidence/review-handshake-round1-2026-08-23.txt`.

## The handshake slice, first correction — 2026-08-23

**I CLAIMED A CLOSED SURFACE AND BUILT TWO DENY LISTS.** §2.2 says withholding
by default costs nothing while "advertising by default means every future SDK
release silently widens the boundary" — and I wrote that widening into both
guards while quoting the sentence three lines above them. `session/reuse`, the
frozen contract's own example of a capability that does not exist, passed the
outbound guard. Both are allow lists now: the outbound surface admits only the
eight methods that exist in 1.0, and the client surface denies EVERY method,
because there is nothing to enumerate when no client capability is advertised
at all.

**ONE FUNCTION WAS ANSWERING TWO QUESTIONS.** Which client capabilities are
served (none) and which agent-origin calls are accepted (one) are different
questions, and `session/update` — the single member of the required five that
flows agent-to-client — belongs to the second. `routeAgentOriginCall` owns it
now, and the migrated assertion sits there rather than being dropped.

**ONE CONSTANT FOR TWO DIFFERENT DOCUMENTS.** §2.2's wire document is
`{ "fs": {}, "terminal": false }` with both filesystem members ABSENT, because
the pinned SDK declares them optional; the agent-session schema separately
records a normalized snake-case summary with both explicitly false. Emitting
the durable summary onto the transport sent field names ACP does not have.
Two representations, two names, and a case asserts they differ.

**ABSENCE IS HOW THE WIRE WITHHOLDS.** An `fs` member present at all — even
set `false` — is denied, because it is a member ACP's optional type did not
have to carry, and this boundary is the one place that difference is still
visible. The comparison is structural rather than serialized, because JSON
member order carries no meaning and a rule that depends on it is a rule about
insertion rather than content.

### Recorded

Four existing cases were migrated on the review's explicit case-specific
authority, each preserving its withholding, fresh-copy or routing assertion
under the corrected name. W641 at
`work/records/2026/08/finding-acp-client-capability-wire-profile-conflation/`
owns the frozen-artifact conflict between the model, the schema and §2.2; this
slice follows §2.2's wire text and the pinned SDK declaration as the review
directs and rewrites neither artifact.

## Independent re-review of the first handshake correction — 2026-08-23 (baton.codex)

**Changes requested for plan item 4t.** The distinct wire/durable capability
documents, structural comparison, negotiation output, default-closed unknown
methods, wholly denied client-call surface and distinct accepted
`session/update` agent-origin route are accepted. One directional overlap
remains: `checkOutboundMethod` still admits `session/update` because its allow
list is all five bidirectional endpoint requirements plus the optional
methods, even though the correction and pinned SDK both classify
`session/update` as agent-origin/client-directed.

Keep the five-member handshake requirement, but make the relay-outbound list
the other four required names plus the three optional names and prove it is
disjoint from the agent-origin list. Focused 19/20; full v12 574/575; only the
one additive re-review regression fails. Review:
`review-2026-08-23T17-39-42Z.md`; evidence:
`evidence/re-review-handshake-round2-2026-08-23.txt`.

## Independent re-review of the corrected handshake — 2026-08-23 (baton.codex)

**Accepted:** the wire/durable split, structural validation, default-closed
unknowns in both directions, the denied client-call surface, and the separate
`session/update` agent-origin route.

**Observed — changes requested.** One directional P1: `KNOWN_AGENT_SURFACE`
was still built as all five required plus three optional, so the relay-
outbound allow list still admitted `session/update` in the reverse direction
and the two claimed closed directional surfaces overlapped. The pinned SDK
1.3.0 places `session/update` in `CLIENT_METHODS` and the other four required
names in `AGENT_METHODS`. One additive regression; gate 574/575. Review and
evidence: `review-2026-08-23T17-39-42Z.md` and
`evidence/re-review-handshake-round2-2026-08-23.txt`.

## The handshake slice, second correction — 2026-08-23

**§2.3's FIVE-MEMBER BASELINE IS NOT A RELAY-OUTBOUND LIST.** It says what an
endpoint must PRESENT across both directions. Building the outbound allow list
from it put `session/update` — a notification the agent sends — into a
client-to-agent surface, one round after separating the inbound route on the
grounds that direction answers a different question.

**SO THE OUTBOUND SURFACE IS DERIVED, NOT TRANSCRIBED.**
`RELAY_OUTBOUND_SURFACE` is the required baseline MINUS what the agent
originates, plus the three optional relay-origin methods — seven names — so
the two directional lists cannot drift apart under a later edit to either.
The constant is renamed on the review's authority so the direction lives in
the name rather than in a comment.

**AND THE TWO SURFACES PARTITION THE BASELINE, not merely avoid each other.**
Disjointness alone would let a required name be dropped from both lists
unnoticed. Between them they account for every required member, and no
agent-origin name may appear that is not part of the baseline.

### Recorded

Revalidated against the pinned `@agentclientprotocol/sdk` 1.3.0 declaration
rather than the prose — `CLIENT_METHODS` carries `session_update`,
`AGENT_METHODS` carries `initialize`, `session/new`, `session/prompt`,
`session/cancel` and all three optional names. That is twice in this slice
that the frozen artefact settled a question the section text alone did not.

## Independent sign-off of the second handshake correction — 2026-08-23 (baton.codex)

**Signed off for plan item 4u.** The five-member endpoint baseline remains the
handshake requirement, while the relay-outbound list is derived as its four
relay-origin members plus the three optional methods. `session/update` is
refused in the reverse direction and retained through the separate
agent-origin route. The focused suite proves the two directional lists
partition the baseline, preserving both disjointness and coverage.

Focused handshake gate 21/21, full v12 gate 576/576, and whitespace clean. No
further findings in this bounded slice. §6.5, adapter composition/contracts,
permission handling and transport-ambiguity re-identification remain open;
W543 and W641 retain their independent contract defects. Review:
`review-2026-08-23T17-48-38Z.md`; evidence:
`evidence/signoff-handshake-round2-2026-08-23.txt`.

## Independent sign-off of the handshake slice — 2026-08-23 (baton.codex)

**Signed off for plan item 4u,** with no further findings in the bounded
slice. `REQUIRED_AGENT_METHODS` remains five for handshake validation,
`RELAY_OUTBOUND_SURFACE` is derived as the four relay-origin required names
plus three optional methods, `session/update` is refused outbound and retained
through `routeAgentOriginCall`, and the two directional lists partition the
required baseline. Focused 21/21, full v12 576/576. Review and evidence:
`review-2026-08-23T17-48-38Z.md` and
`evidence/signoff-handshake-round2-2026-08-23.txt`.

## The session-axis slice — 2026-08-23

**NOTHING WAS WRITING THE AXIS.** The turn slice reads `agent_sessions.state`
and the event slice deliberately does not, but only `openAgentSession` and
`closeAgentSession` ever wrote it — so seven of the nine states were
unreachable, and the turn slice's own record said so. §7.3's successor table
is implemented now, decided inside the write transaction because a read
followed by a separate write is not a monotone axis across two managers.

**A SELF-OBSERVATION IS NOT A MOVE.** Observing the same state twice is
ordinary, and refusing it would make a duplicate look like a regression — the
reading the event slice already rejected for frames.

**`agent-quiescent` CANNOT REACH `unknown`, AND THAT IS THE INTERESTING
EDGE.** It means a terminal turn fact WAS observed after cancellation was
ordered, so the ending is known; `unknown` there would be a regression in
knowledge rather than the honest absence of it. `unknown` never becomes
`closed` for the mirror-image reason.

### Observed — a conflict between §7.3 and signed-off code, filed not fixed

`closeAgentSession` sets `state = 'closed'` for any row not already closed,
and four of those edges are forbidden by the frozen table — `not-started`,
`prompting`, `cancel-requested` and, most seriously, `unknown`, which §3.3
names as recording knowledge that was never acquired. Measured with the
retained probe `evidence/probe-close-session-axis-2026-08-23.mjs`; output in
`evidence/observed-close-session-axis-conflict-2026-08-23.txt`.

**It is deliberately not corrected here.** Existing signed-off cases close
freshly opened sessions to free the posture, so routing close through the axis
would fail them — and editing signed-off assertions to match a new module is
the move this Work has already corrected twice. More importantly there is a
contract question underneath: the partial unique index frees a posture only at
`closed`, while the frozen table lets a never-initialized session end only at
`unknown`, which by deliberate design does not free it. Either the table needs
an edge, or `closeAgentSession` needs a different lifecycle, or posture
freeing must stop depending on `closed`. **This needs an owning record**, as
the tool-call `kind` and client-capability conflicts did before they became
W543 and W641. The new module papers over nothing: it refuses every forbidden
edge, and the conflict is that one existing function does not go through it.

### Recorded

Two validations **mutually mask**, and discovering it fixed a gap in the case
file rather than in the code: the one input where neither covers for the other
is observing an invented state against a row already holding that same
invented state, because the self-observation shortcut answers before anything
is proved. A zero-witness mutation is a claim about the code; this time it was
a claim about the test.

## Independent first review of the session-axis slice — 2026-08-23 (baton.codex)

**Changes requested for plan item 4w.** The exact frozen state/successor table,
all-pairs decision, transactional durable move, no-op self-observation,
terminal regression behavior, closed malformed-state errors and permanent
separation from runtime quiescence are accepted.

One P1 remains: `observeAgentSessionState` discards the provider-session id
from the full §3.1 reference and does not validate the reference before SQL.
A wrong label can therefore move or affirm another provider session's axis,
while malformed input can escape as a raw SQLite `TypeError`. Normalize the
full reference, bind stored provider id before both no-op and move decisions,
and leave the row unchanged on either closed refusal. Focused 12/14; full v12
588/590; only the two additive review regressions fail.

The separately measured close/posture-release contradiction now has its own
owner, W771 at
`work/records/2026/08/finding-agent-session-close-axis-conflict/`. It does not
authorize a local table or close-path rewrite, but final W4 composition must
revalidate its disposition. Review: `review-2026-08-23T18-02-11Z.md`;
evidence: `evidence/review-session-axis-round1-2026-08-23.txt`.

## Independent first review of the session axis — 2026-08-23 (baton.codex)

**Accepted:** the exact nine-state table, all eighty-one pairs, transactional
durable moves, the no-op self-observation, terminal behaviour, the
malformed-state taxonomy, and the permanent separation from runtime
quiescence.

**Observed — changes requested.** One P1: `observeAgentSessionState` discards
`providerSessionId` and does not prove the reference before its query, so a
wrong label can move or affirm another provider session's axis and malformed
input escapes as a raw SQLite error. Two additive regressions; gate 588/590.
Review and evidence: `review-2026-08-23T18-02-11Z.md` and
`evidence/review-session-axis-round1-2026-08-23.txt`.

**And the `closeAgentSession` conflict now has a durable owner:** W771 at
`work/records/2026/08/finding-agent-session-close-axis-conflict/`, high
priority. The review does not authorize changing the frozen successor table,
weakening signed-off close assertions or papering over `unknown`; independent
W4 slices continue, and **final W4 composition must revalidate W771's
disposition**.

## The session-axis slice, first correction — 2026-08-23

**BINDING THREE QUARTERS OF A REFERENCE IS NOT BINDING IT — FOR THE THIRD
TIME.** §3.1 makes the provider session id the fourth component. The turn
boundary binds it; the event write path binds it; the event READ path did not
and was corrected two rounds ago in exactly these words. Then this module was
written binding three quarters.

What makes it repeatable is that the missing component authorizes nothing, so
its absence never breaks a happy path: the row is found, the state moves,
every ordinary case passes. Eighty-one exhaustively driven transition pairs
said nothing about it, because not one of them was about identity. Exhaustive
coverage of the wrong axis is not coverage.

**AND A NO-OP IS STILL AN OBSERVATION.** Affirming that provider session B's
axis reads `prompting` is a claim about B, and answering it from A's row is
the same mistake as moving A's row. The binding therefore precedes the
self-observation shortcut rather than sitting after it — a correction that
only thought about MOVES would have put it one line later and passed every
move-shaped case.

### Recorded

W771 is acknowledged and untouched: nothing here changes the frozen successor
table, weakens a signed-off close assertion or papers over `unknown`. **Final
W4 composition must revalidate W771's disposition**, and this correction does
not discharge that.

## The session-axis slice, correction sign-off — 2026-08-23

**Confirmed.** Independent review accepted item 4x. The complete four-part
session reference is proved before SQL, and the stored provider id is compared
inside the write transaction before either a no-op answer or a move decision.
Malformed references close as `integrity.schema`; either direction of label
disagreement closes as `runtime-observation.identity-mismatch`; neither moves
the axis. Focused session-axis 16/16, full v12 592/592, whitespace clean.

This sign-off is bounded to frozen §7.3-§7.4. W771 remains the sole owner of
the `closeAgentSession` versus frozen-axis/posture-release conflict, and final
W4 composition must revalidate its disposition. Review:
`review-2026-08-23T18-11-15Z.md`; evidence:
`evidence/signoff-session-axis-round2-2026-08-23.txt`.

## Independent sign-off of the session axis — 2026-08-23 (baton.codex)

**Signed off for plan item 4x.** Full §3.1 reference validation precedes SQL,
and the stored provider identity is compared inside `BEGIN IMMEDIATE` before
both the no-op and the move decisions. Focused 16/16, full v12 592/592. W771
remains untouched and **mandatory to revalidate at final W4 composition**.
Review and evidence: `review-2026-08-23T18-11-15Z.md` and
`evidence/signoff-session-axis-round2-2026-08-23.txt`.

## The reconnect slice — 2026-08-23

**A LOST TRANSPORT ENDS THE EPOCH.** §8.4's reasoning is specific rather than
general caution: a turn in flight when the transport died may have completed,
partially completed or not started, and it had a WRITABLE WORKSPACE.
Re-prompting a fresh session with the same content would re-run side effects
the manager cannot enumerate, against a workspace that already holds the first
attempt's partial output.

**`ambiguous.operation`, NOT `refused.precondition`.** The manager is not
saying the re-prompt is malformed or out of order — it is saying it cannot
KNOW what the first attempt did. The closed pair carries that to a caller who
never read §8.4, and the prompt argument is ignored on purpose: a signature
accepting nothing would invite the belief that some other prompt might be
acceptable.

**THE OUTCOME IS REPORTED AND NOT RECORDED.** `recordTurn` needs an allocated
token, a prompt digest and the supervision window, and this boundary holds
none of them; inventing them here would be minting evidence about a turn it
never saw.

**AND WHETHER A TURN WAS IN FLIGHT IS STATED.** It decides an outcome, and
§5.4 spends a section on what an outcome may not be derived from — so a
non-boolean is `integrity.schema` rather than something truthy.

### Recorded

**The re-identification GATE is not built; its FLAG is.** W151 §9's positive
runtime re-identification belongs to another Work and needs runtime inspection
this slice does not have. `nextEpochAllowedWithoutRuntimeReidentification:
false` is an explicit answer rather than an absence, so a later slice that
mints an epoch contends with a recorded `false` instead of a gap in a section
it may not have read. `nextEpoch` is untouched and this slice adds no gate to
it — named so the boundary is not mistaken for one.

This is also the first slice that COMPOSES two earlier ones: transport loss is
the ordinary way an epoch reaches `unknown`, and until the session axis landed
there was no boundary to move it through. The identity question was asked of
this boundary explicitly, which is the commitment the axis correction ended
on.

## Independent first review of reconnect ambiguity — 2026-08-23 (baton.codex)

**Changes requested for plan item 4z.** The `unknown` state decision,
idempotent re-observation, explicit turn-outcome selection, refusal to invent a
turn record, `ambiguous.operation` re-prompt refusal, and reachability versus
re-identification separation are accepted.

Two P1 boundary defects remain. First, `handleTransportLoss` re-reads and
spreads the caller-owned session reference after the axis commits. A shifting
getter can move provider A's axis while the answer labels provider B, and
arbitrary extra members escape the frozen reference's closed shape. Snapshot
the four members once and use that same owned reference for both observation
and answer. Second, the options container is not validated: `null` leaks a raw
`TypeError`, while boolean, string, and array values silently default the
outcome fact and commit `unknown`. Supplied malformed containers must close as
`integrity.schema` before any move. Retain both additive regressions.

**Clarification:** the returned `nextEpochAllowedWithoutRuntimeReidentification`
flag is not recorded and does not gate `nextEpoch`. It is accepted here only
as a reported fact; full §8.4 enforcement remains dependent on the explicitly
deferred W151 §9 integration.

Focused 9/11 and full v12 601/603; only the two review regressions fail.
Review: `review-2026-08-23T18-21-55Z.md`; evidence:
`evidence/review-reconnect-round1-2026-08-23.txt`.

## Independent first review of the reconnect slice — 2026-08-23 (baton.codex)

**Accepted:** the `unknown` transition, idempotence, the explicit outcome, the
absence of a fabricated turn record, the `ambiguous.operation` re-prompt
refusal, and the reachability separation.

**Observed — changes requested.** Two P1. After committing provider A to
`unknown`, the answer re-read and spread the caller's reference and could
report provider B plus extra members. And the options envelope was unproved:
`null` leaked a `TypeError`, while boolean, string and array inputs silently
defaulted `turnInFlight` and committed `unknown`. Two additive regressions;
gate 601/603. The next-epoch flag is reported, not durable enforcement.
Review and evidence: `review-2026-08-23T18-21-55Z.md` and
`evidence/review-reconnect-round1-2026-08-23.txt`.

## The reconnect slice, first correction — 2026-08-23

**TWO READS OF ONE UNTRUSTED VALUE, ONE DECIDING AND ONE REPORTING.** The axis
validated and bound its own normalized copy; the answer then spread the
caller's object again. A getter could answer provider A to the check that
committed the epoch and provider B to the record of it, and members the closed
§3.1 shape does not have rode along into something that looks like a session
reference. `store.mjs` already carries this exact lesson — "a `toJSON` method
can return `{diagnostic: <bearer>}` while `Object.entries` shows only the
method" — and it was written again at a new boundary.

`normalizeAgentSessionRef` is exported now, the reference is proved ONCE, and
the same object goes to the axis and into the answer. The proof also moved
BEFORE the durable observation, so a malformed reference cannot commit an
epoch and then be refused on the way out.

**A DEFAULT IS FOR AN ARGUMENT NOBODY GAVE, NOT ONE SOMEBODY GAVE WRONGLY.**
`{ ... } = {}` defaults only for `undefined`, so an explicit `null` reached a
property read and a boolean, string or array destructured to `undefined`, took
the `false` default, and committed the epoch on operands nobody proved.

**AND THE FIRST FIX MADE THE SAME MISTAKE ONE LEVEL DOWN.**
`options?.turnInFlight ?? false` turns an explicit `null` member into the
default. The case already written for this slice — that whether a turn was in
flight is STATED rather than inferred — failed immediately and caught it. The
member is read only when the key is present.

### Recorded

One mutation is measured rather than counted: the answer's copy is
**equivalent**, because the snapshot is created here and nothing else holds
it. It is kept because a boundary that hands back the object it validated
against is one edit away from handing back the object it is still using.

The next-epoch flag remains REPORTED and not durable enforcement; W151 §9's
gate stays deferred and W771 stays mandatory at final W4 composition.

## Independent re-review of reconnect correction — 2026-08-23 (baton.codex)

**The original two P1s are closed.** The session reference is snapped before
mutation and reused for the observation and exact four-member answer; the
primitive/null/array options and explicit non-boolean members now close before
the axis moves. The unchanged axis suite is 16/16.

**One P1 remains.** The envelope guard equates every non-array object with an
options document. Dates, Maps, regular expressions, class instances and
inherited-property bags all take the absent-member default and commit
`unknown`. That is still a supplied wrong argument being treated as an absent
one. Require a plain record (ordinary or null prototype), test
`turnInFlight` as an own member, and refuse non-records as `integrity.schema`
before mutation. Retain the additive re-review regression.

Focused 13/14; full v12 605/606; only the new regression fails. Review:
`review-2026-08-23T18-32-05Z.md`; evidence:
`evidence/re-review-reconnect-round2-2026-08-23.txt`.

The next-epoch flag remains reported rather than durable enforcement; W151
§9 stays deferred, and W771 remains mandatory at final W4 composition.

## Independent re-review of the corrected reconnect slice — 2026-08-23 (baton.codex)

**Accepted:** the one-read exact reference ownership, the snapshot before the
durable observation, and the fresh four-member answer. The signed-off axis is
unchanged apart from exporting its normalizer.

**Observed — changes requested.** One P1: the envelope guard accepts every
non-array object, so a Date, a Map, a regular expression, a class instance and
an inherited-member object take the absent default and commit `unknown`. One
additive regression; gate 605/606. Review and evidence:
`review-2026-08-23T18-32-05Z.md` and
`evidence/re-review-reconnect-round2-2026-08-23.txt`.

## The reconnect slice, second correction — 2026-08-23

**I WROTE THE RULE AND THEN IMPLEMENTED ITS OPPOSITE.** The previous round's
finding was "a default is for an argument nobody gave, not an argument
somebody gave wrongly". That sentence went into the code, and the check under
it was `typeof options !== "object" || Array.isArray(options)` — true of a
Date, a Map, a regular expression and every class instance. The defect the
paragraph describes survived the fix aimed at it, because "not a primitive and
not an array" is not "is a record".

**AND IT IS THE THIRD ALLOW-RULE IMPLEMENTED AS A DENY-RULE IN THIS WORK.**
The handshake slice's two method surfaces were the first two, and that
correction records why: a deny list "silently widens when an SDK adds a
method". A type test admitting everything except two known shapes widens the
same way, on the day a caller passes a shape nobody listed.

**A RECORD IS A PROTOTYPE TEST**, because it is the only test that
generalizes. `Object.create(null)` is admitted deliberately — it carries no
class and no behaviour — and a promise, a typed array and a boxed string are
refused for the rule rather than by enumeration.

**AND WHAT WAS GIVEN IS WHAT IS ON THE OBJECT.** `in` walks the prototype
chain, so the optional member is read with `hasOwnProperty`.

### Recorded

**The reviewer's case corrected my case.** I first wrote the ownership test as
`Object.create({ turnInFlight: true })` taking the absent default; the
reviewer's own case lists that shape among those that must REFUSE, and the
prototype rule refuses it before ownership is asked. I changed my case to
match the ruling rather than the other way round, then found the input that
actually exercises ownership — a plain record whose `turnInFlight` lives on
`Object.prototype` itself, which is prototype pollution. Without that case the
own-member rule would have been unwitnessed defence.

This round also closes the failure W771's handoff named and left standing: it
belonged to W4's open round, and it is fixed in the record that owns it.

## Independent third review of the reconnect correction — 2026-08-23

**Accepted:** item 4ab closes the plain-record P1. Ordinary and
null-prototype records are admitted; Dates, Maps, regular expressions, class
instances and custom-prototype bags refuse before mutation; and the optional
member is read only when it is owned. The prior reference and §8.4 corrections
remain intact.

**Observed — changes requested.** One P2 remains in the refusal path itself.
The non-boolean-member diagnostic serializes the rejected value, so a BigInt
leaks raw `TypeError`. The new non-record diagnostic reads the rejected
value's prototype constructor, so an accessor there executes and leaks its
arbitrary exception. Refusal diagnostics must use inert bounded type facts,
must not serialize or inspect caller behavior, and must translate unavoidable
reflection failure to `integrity.schema`. Both additive regressions leave the
session axis unchanged at `prompting`.

Focused reconnect is 16/18; the signed-off axis remains 16/16. The current
full v12 gate is 624/631: these two W4 failures plus the five open W771
regressions already owned by W771. Review and evidence:
`review-2026-08-23T18-55-02Z.md` and
`evidence/review-reconnect-round3-2026-08-23.txt`.

## Independent third review of the reconnect slice — 2026-08-23 (baton.codex)

**Accepted:** item 4ab closes the plain-record P1.

**Observed — changes requested.** One P2 in refusal diagnostics:
`JSON.stringify` on a rejected BigInt leaks a raw `TypeError`, and `describe()`
reads an untrusted prototype's `constructor` getter and leaks its arbitrary
`Error`. Both leave the axis unchanged and neither returns the closed pair.
Review and evidence: `review-2026-08-23T18-55-02Z.md` and
`evidence/review-reconnect-round3-2026-08-23.txt`.

## The reconnect slice, third correction — 2026-08-23

**A REFUSAL MUST NEVER RUN THE VALUE IT IS REFUSING.** `describe()` did not
exist before the previous round — I added it so a refusal would not read
"{} is not an options document" when a caller passed a Map. It serialized the
rejected value and read its prototype's `constructor`, so at the exact moment
the boundary had DECIDED to refuse, it ran the rejected value's behaviour and
lost the decision.

That is the same shape as the two P1s it was written alongside — an operand
reaching a boundary that had not proved it — with the aggravating detail that
this operand had already been proved unacceptable. Diagnostics are where the
temptation lives, because a better message needs to know more about the value
and knowing more means touching it.

**SO THE FACTS ARE INERT AND DELIBERATELY COARSE.** `typeof`,
`Array.isArray`, and a prototype comparison; nothing serialized, no property
of the value or its prototype read. A diagnostic that has to be exactly right
about an untrusted value is a diagnostic that has to touch it.

### Recorded

Two measurements rather than a count. Removing the reflection wrapper ALONE
fails no case — `getPrototypeOf` does not throw on any ordinary value, so it
is defence against host and Proxy exotica and is not counted as a guard.
Re-adding the constructor read alone is caught BY that wrapper. What the cases
witness is the pair, and the guard that carries the finding is not reading the
constructor at all.

**And my own case asserted an outcome instead of a rule.** I expected a plain
record carrying a throwing `Symbol.toStringTag` to be REFUSED; its prototype
is `Object.prototype` and it has no own `turnInFlight`, so the plain-record
rule accepts it and the absent default applies — correctly. The case now
asserts the rule, and that reaching the default ran nothing.

## Independent fourth review of the reconnect correction — 2026-08-23

**Accepted:** item 4ac closes both prior P2 reproductions. Rejected values are
no longer serialized, the hostile prototype constructor is not read, coarse
diagnostics remain useful, and ordinary refusal paths retain the closed pair
without moving the session axis.

**Observed — changes requested.** One P2 remains at the preceding decision.
`isPlainRecord` performs an unwrapped `Object.getPrototypeOf` before the
formatter's wrapped comparison, so a Proxy prototype trap still leaks its
arbitrary exception. And an accepted plain record's own `turnInFlight`
accessor is executed as though it were document data. Snapshot the prototype
once inside the translated boundary; inspect the optional member through one
guarded own-property descriptor; accept only absence or a data descriptor;
and translate reflection failures without invoking accessors.

Focused reconnect is 21/23. Full v12 is 633/642: these two W4 failures, two
separately owned W543 failures, and five separately owned W771 failures.
Review and evidence: `review-2026-08-23T19-13-23Z.md` and
`evidence/review-reconnect-round4-2026-08-23.txt`.

## The reconnect slice, fourth correction — 2026-08-23

**A RULE APPLIED AT THE SECOND OF TWO SITES IS NOT APPLIED.** The previous
round established that a refusal must never run the value it is refusing, and
wrote that translating an unavoidable reflection failure was cheaper than
proving no Proxy could make `getPrototypeOf` throw. Then it wrapped the
reflection in `describe` and left the one in `isPlainRecord` bare — and
`isPlainRecord` runs first, so a trapping Proxy leaked past the guard that had
just been written for it. One translated snapshot now, taken once and shared.

**AND `hasOwnProperty` IS INERT WHILE THE READ AFTER IT IS NOT.** Checking
ownership runs nothing, so the whole step read as safe — but the property read
that followed executes an own ACCESSOR, so an ACCEPTED plain record could
still run the caller's code at a boundary whose entire rule is that it does
not. One guarded own-property DESCRIPTOR is read now, and only absence or a
data descriptor is an operand: a document carries data, and a getter is a
program.

### Recorded

One mutation is measured rather than counted, and the distinction is the
point: an accessor's descriptor has no `value`, so the boolean proof
downstream already refuses it with the same pair. What keeps the getter from
RUNNING is reading the descriptor instead of the property, and that mutation
fails six cases. The accessor branch supplies the message, not the guard.

## Independent fifth review of the reconnect correction — 2026-08-23

**Accepted:** item 4ad closes the two exact preceding cases. The record test
and description share one translated prototype snapshot, and an own accessor
is refused without execution. All earlier reconnect corrections remain green;
the adjacent session axis is 16/16 and turn suite is 50/50.

**Observed — changes requested.** One P2 remains at two diagnostic edges.
`Array.isArray` throws on a revoked Proxy, so both a revoked options envelope
and a revoked data-member value escape the closed pair through `describe()`.
And the descriptor-reflection catch interpolates `failure.message`, executing
a getter on the arbitrary thrown value and leaking its exception. Translate
every potentially throwing classification operation and form catch messages
only from manager-owned text.

Focused reconnect is 25/27. Full v12 is 646/652: these two W4 failures plus
two separately owned W543 and two separately owned W641 failures. W771's
posture-slot suite is green at 25/25 in the same full run. Review and evidence:
`review-2026-08-23T19-42-22Z.md` and
`evidence/review-reconnect-round5-2026-08-23.txt`.

## Fifth correction: reflection is not the same as caller code — 2026-08-23

**The operation that was failing was the one every comment had cleared.**
`describe()` had said for two rounds that "`typeof` and `Array.isArray` invoke
nothing". That is true, and it is not the property that matters: array
classification follows a Proxy to its target, so `Array.isArray` THROWS on a
revoked Proxy. It sat outside the translated boundary on both the envelope and
the member path and leaked a raw `TypeError` at the moment the boundary had
already decided to refuse.

Four rounds of findings on this primitive have all been "a refusal must not run
what it refuses", and I had been reading that as being about executing CALLER
CODE. This operation runs none and fails anyway. **"Runs no user code" is not
"cannot fail".** Every classification is taken through one guarded helper now,
and `typeof` is the only operation still named as exempt, because it is the
only one that genuinely cannot throw.

**And a catch that establishes a refusal does not interview what was thrown at
it.** `ownTurnInFlight` interpolated `failure.message`; JavaScript permits
throwing any value, so that is a property read on an object the caller chose,
and an accessor there runs the caller's code inside the refusal. The catch
takes no binding and the text is the manager's own.

**Beyond the review, and recorded rather than folded in:** with array
classification in the snapshot it became visible that `isPlainRecord` decided
documenthood from the prototype alone, so a Proxy over an array whose
`getPrototypeOf` trap answers `Object.prototype` was a valid options envelope.
An array is not a document however it is dressed; the rule is tested now
instead of inferred from a prototype a Proxy is free to lie about.

Verification: reconnect 29/29, axis 16/16, turn 50/50, posture slots 25/25;
full v12 654/656 with both remaining failures belonging to W641's open round;
design models 64/66/24/74; v11 pytest 2980 and serial 52; codex-event-bridge
336; acp-baton-bridge 55; whitespace clean; zero test-owned roots under a
TMPDIR bracket. Evidence:
`evidence/correction-reconnect-round5-2026-08-23.txt`.

## Independent sixth review of the reconnect correction — 2026-08-23

**Accepted:** item 4ae closes both exact fifth-review edges. Revoked Proxy
classification is translated, the descriptor catch no longer reads what was
thrown, and bare or dressed arrays refuse as arrays.

**Observed — changes requested.** One P1 remains on the successful-trap path.
A Proxy over an ordinary object can run `getPrototypeOf`, answer
`Object.prototype`, run `getOwnPropertyDescriptor`, answer absence, and be
accepted as a plain options document; `handleTransportLoss` then commits
`unknown`. A Proxy member likewise runs its prototype trap before the refusal.
The contract admits ordinary/null-prototype records, not behavioral Proxies;
translated exceptions do not protect against successful traps. Reject
Proxies through a non-observing discriminator before reflection on both paths.

Focused reconnect is 29/31. The adjacent axis, turn and posture suites are
16/16, 50/50 and 25/25. Full v12 is 654/658: these two W4 failures and two
separately owned W641 failures. Review and evidence:
`review-2026-08-23T20-09-23Z.md` and
`evidence/review-reconnect-round6-2026-08-23.txt`.

## Sixth correction: a trap that answers — 2026-08-23

**Five rounds went into making reflection fail safely, and the hole was the
ordinary case.** Every guard on this primitive assumed a hostile value
MISBEHAVES — it throws from a getter, from a trap, it is unserializable, it
revokes itself — and each round translated one more failure. A Proxy over `{}`
needs none of that: it runs `getPrototypeOf`, returns `Object.prototype`, runs
`getOwnPropertyDescriptor`, returns no member, and is accepted as an empty
options document. Caller code ran, and a program committed the epoch to
`unknown`.

**Translating a trap that throws does nothing about a trap that answers.**

The Proxy test is therefore FIRST and NON-OBSERVING — `node:util/types.isProxy`
reads an internal slot and runs no trap, identifying live and revoked Proxies
alike. Another try/catch would not do: a successful trap walks past one. A
Proxy is a program wearing an object, and the rule this envelope has always
stated is that a document has no behaviour. One guard covers the envelope and
the member path because both classify through the single helper the fourth
correction introduced.

**Raised for a ruling rather than decided here.** The same defect exists on a
session REFERENCE, and it is measured rather than suspected: a Proxy reference
runs four `get` traps in `normalizeAgentSessionRef` and is accepted. That is
the signed-off axis, on every observation path in this manager, so refusing
Proxy references is a cross-cutting behavior change rather than a two-case
correction. The DISAGREEMENT attack there is already closed — the axis takes
one owned copy — but caller code still runs.

**And the fork is now proven rather than predicted.** `agent_handshake.mjs`
grew its own copy of these rules, and W641's second review has just found the
same Proxy defect in that copy. Two implementations of one rule earned the same
finding twice; one shared record primitive at W4 composition is the answer.

Verification: reconnect 32/32, axis 16/16, turn 50/50, posture slots 25/25;
full v12 662/664 with both remaining failures belonging to W641's second
review; design models 64/66/24/74; v11 pytest 2980 and serial 52;
codex-event-bridge 336; acp-baton-bridge 55; whitespace clean; zero test-owned
roots under a TMPDIR bracket. Evidence:
`evidence/correction-reconnect-round6-2026-08-23.txt`.

## Independent sign-off of the sixth reconnect correction — 2026-08-23

**Signed off for item 4af.** A non-observing Proxy discriminator now precedes
all reflection, both reconnect paths refuse live and revoked Proxies without
running traps or moving the axis, and ordinary/null-prototype data records
remain accepted. Both sixth-review regressions pass, along with the broader
all-thirteen-traps property. The marked dressed-array diagnostic migration is
correct: a Proxy is rejected before array classification while a bare array
is still named as an array.

**Separate open decision.** `normalizeAgentSessionRef` still accepts a Proxy
reference and runs four `get` traps. Item 4aa deliberately chose one owned
snapshot to stop a shifting getter from disagreeing between validation and
reporting, so declaring references inert now would supersede that accepted
boundary. Final W4 composition must decide explicitly whether §3.1 references
are inert data records or structural values read once. If inert, use W641's
shared record primitive and prove exact own data members; rejecting Proxies
alone while ordinary accessors still run is not the general rule.

Focused reconnect/axis/turn/posture suites are 32/16/50/25. Full v12 is
662/664, with both failures owned by W641's open handshake correction. Review
and evidence: `review-2026-08-23T20-28-51Z.md` and
`evidence/signoff-reconnect-round6-2026-08-23.txt`.

## Independent review of final composition — 2026-08-23

**Accepted:** item 4ai genuinely consumes W641's shared record primitive, and
its dependency mutations witness that connection; item 4al makes the two
§3.1 copies agree on the already-frozen empty-provider-id rule. The additive
review witness also establishes that every one of item 4aj's 162 hostile
taxonomy cells actually refuses, rather than merely checking a closed pair if
a call happens to throw.

**Observed — changes requested.** Item 4ak proves only that read identifiers
are nonempty strings, not that they satisfy frozen `opaqueId`: spaces and
values longer than 160 characters pass through to SQLite and become false
absence or precondition answers. And item 4aj bounds string diagnostics while
leaving caller-sized Symbol descriptions and BigInts unbounded; measured
1,000-character values render at 1,008 and 1,000 characters. Share the frozen
opaque-id proof across the read operands and bound every primitive rendering.

**Proposed ruling, still open:** make an in-process session reference the same
exact inert four-member data record as its frozen document form, using W641's
shared primitive and the frozen member bounds. If approved, explicitly mark
item 4aa's structural one-read boundary superseded. This recommendation is
decision support, not a reviewer assumption of product authority.

Full v12 is 678/680, with only the two additive W4 reviewer regressions
failing. Review and evidence: `review-2026-08-23T20-55-23Z.md` and
`evidence/review-composition-round1-2026-08-23.txt`.

## Independent review of the composition correction — 2026-08-23

**Accepted:** the opaque-id proof is complete and shared across the five
current boundaries; malformed identity no longer becomes absence or business
state; `nameValue` bounds the rendering rather than one favored input branch;
and the turn boundary delegates to the one §3.1 normalizer. All three prior
review regressions pass.

**Observed — changes requested.** The new provider-session `maxLength: 512`
proof uses JavaScript `.length`, which counts UTF-16 code units, while JSON
Schema measures Unicode characters. A 512-character astral provider id has
1,024 code units, is accepted by the frozen schema, and is refused by the
normalizer. Measure in the frozen contract's unit and retain the additive
512/513 Unicode-bound rows.

Focused taxonomy is 8/9 and full v12 is 681/682, with only the new provider-id
case failing. Review and evidence: `review-2026-08-23T21-08-54Z.md` and
`evidence/review-composition-round2-2026-08-23.txt`.

## Independent review of the Unicode-ruler correction — 2026-08-23

**Accepted:** the provider-session proof now uses the frozen JSON Schema's
Unicode-code-point unit, the 512/513 astral boundary agrees at both consumers,
opaque-id diagnostics use the truthful unit, and character-safe truncation no
longer emits half a surrogate pair.

**Observed — changes requested.** The bounded diagnostic performs a short
limit probe and then `[...text]` materializes the entire caller-sized string
before slicing its first 60 characters. Measured: a 1,000-character input
causes 1,063 iterator yields for a 61-character answer. Build the prefix with
an early-stopping pass so discarded content does not cause proportional array
allocation and traversal.

Focused taxonomy is 10/11 and full v12 is 683/684, with only the additive
discarded-tail case failing. Review and evidence:
`review-2026-08-23T21-19-33Z.md` and
`evidence/review-composition-round3-2026-08-23.txt`.

## Independent sign-off of the discarded-tail correction — 2026-08-23

**Signed off for item 4as.** `bounded()` now returns ordinary short strings
without iteration, visits at most 61 Unicode code points for a long string,
and retains 60 complete code points without materializing the discarded tail.
The additive iterator-count regression passes.

The current full v12 result is 684/687. All three failures are the additive
W1593 record-diagnostic regressions, including the new capability-envelope row
in W4's general refusal-bound property; none reopens item 4as. W1593 owns that
separate correction and is queued at the decision endpoint.

**Still open:** items 4ah/4ao need the product-authority ruling on the
in-process section 3.1 reference container. This sign-off does not infer that
decision. Review and evidence: `review-2026-08-23T21-33-40Z.md` and
`evidence/signoff-composition-round3-2026-08-23.txt`.

## Section 3.1 session references are plain data — confirmed 2026-08-23

Slawomir approves the proposed exact inert-record boundary. An in-process
section 3.1 session reference is plain old data: one ordinary or
null-prototype record carrying exactly the four own enumerable data members
corresponding to `runtime_attempt_id`, `posture`, `session_epoch`, and
`provider_session_id`. Proxies, accessors, arrays, class instances, hidden
members, and extra members are refused without executing caller behavior.

This ruling explicitly supersedes item 4aa's structural one-read container
boundary. Reading an accessor once prevents disagreement between two reads,
but still executes a caller-supplied program where the frozen contract
describes a document. No compatibility is retained for that accidental
permissiveness. A caller holding a richer representation must deliberately
materialize the canonical four-member data record before calling the Worker
Manager.

Implementation uses W641's shared inert-record proof, then validates and
copies the four member values under the already-frozen bounds. This changes
only which JavaScript containers may carry the reference; it does not change
the reference's identity, authority, member types, or session semantics.

## POD survives; host-side JavaScript implementation does not — confirmed 2026-08-23

The campaign's later host-language ruling supersedes the implementation
placement in the preceding section. Exact inert POD remains the required
session-reference contract, but W4 does not extend
`normalizeAgentSessionRef`, W641's JavaScript primitive, or another host-side
Node module to implement it. Those modules and their reviews remain reference
evidence for the Python Worker Manager.

W4 returns to review for a Python implementation boundary that carries forward
the durable store, state machines, replay rules, POD contracts, and portable
acceptance cases already established here. Provider-native JavaScript remains
permitted only inside an isolated worker image; it is not part of this trusted
host-side manager slice.

## Python Worker Manager boundary revalidated — 2026-08-24

**Confirmed:** the frozen Node manager is executable-reference evidence only.
The Python implementation is a separately installable package below
`v12/python/`; it imports neither host-side Node nor v11 and owns a distinct
SQLite control store. Product copies of the two frozen schemas travel as
Python package data, with test-only byte-identity checks against the canonical
dossier assets.

**Confirmed translation of the POD ruling:** Python admits an exact built-in
`dict` carrying exactly the four required section 3.1 members. Dict subclasses,
arbitrary mappings, objects, sequences, missing or extra members, and any
behavior-bearing representation refuse before use. Accepted values are copied
recursively into manager-owned built-ins. Portable refusal prose is owned and
bounded; it never renders an unsupported caller object or retains a schema
library's instance-bearing prose.

**Observed blocker:** no Python source or package exists under `v12`, and no
Python assignment-authority/session implementation exists for W4 to consume.
The repository venv also lacks the required Draft 2020-12 validator. A Python
manager cannot import frozen Node `V12Session`, copy authority state, or depend
on ambient system packages while satisfying the confirmed boundary.

**Proposed resolution:** create a separately owned Python authority
prerequisite, restore authority -> manager scheduling, approve the
`v12/python/` package/toolchain lock, then implement W4 in six independently
reviewed cuts: contracts/POD, store/journal, offers/settlement, attempts and
output/intake, agent-session axes, and public composition. Full evidence:
`evidence/python-boundary-revalidation-2026-08-24.txt`; review:
`review-2026-08-24T04-06-44Z.md`.

## Python package, toolchain and prerequisite approved — 2026-08-24

Slawomir approves the revalidated Python boundary with Python 3.13 as the
trusted-host floor. The product is one separately installable and
self-contained distribution below `v12/python/`: `pyproject.toml` declares
the package and direct dependencies, while `requirements.lock` pins the full
resolved environment with hashes. This v12 lock is independent of the
repository's v11 development requirements.

The distribution may contain both authority and Worker Manager modules, but
that packaging convenience does not collapse ownership. The Python assignment
authority and Python Worker Manager are separate Work, modules, SQLite files,
connections, schemas and transactions. Only the authority mints a
participant-bound session; W4 receives that already-minted capability and
never receives authority bootstrap, configuration, a database handle, or a
store path.

A genuine pinned Draft 2020-12 validator is required. Ambient system packages
are not product dependencies, and a handwritten partial schema validator is
not an accepted substitute. The frozen schema copies are package data and
remain byte-identical to their canonical dossier assets under tests.

The separately owned Python assignment-authority Work is a blocking M2
prerequisite. The frozen Node authority and manager remain executable-reference
evidence only; no trusted host runtime imports or bridges through them. Once
the prerequisite closes, W4 proceeds through the six serial review cuts in
the revalidation rather than one large transliteration.

## Runtime Draft 2020-12 validation approved — 2026-08-24

Slawomir chooses runtime validation, option A from
`evidence/w4-prerequisite-revalidation-2026-08-24.txt`. Worker-control and
agent-session documents cross an untrusted boundary, so the Python Worker
Manager enforces their frozen Draft 2020-12 schemas at runtime. Test-only
validation would replace universal enforcement with corpus coverage, and
postponing validation would knowingly make the first contracts cut partial;
neither alternative is accepted.

Pin `jsonschema` 4.26.0, not the ambient 4.19.2 research installation. Resolve
its complete Python 3.13 runtime closure into `requirements.lock` with hashes
and provision the offline wheelhouse with the exact artifacts. A compiled,
platform-specific dependency wheel is acceptable as a deployment artifact;
the lock remains the authoritative resolution and may carry the hashes needed
by each certified platform.

This ruling specifically supersedes W2845 tests that treated the whole future
distribution as dependency-free. Standard-library-only remains an authority
MODULE invariant: `baton_v12.authority` imports no third-party package. The
distribution lock becomes populated, and the Worker Manager boundary admits
only its explicitly pinned validator dependency. Update those existing test
assertions deliberately; do not weaken the authority isolation checks.

## Retain the frozen Node oracle until Python equivalence — confirmed 2026-08-24

The host-side Node Worker Manager is superseded product code, but it is not
discarded during the Python port. Keep `v12/src/worker_manager/*.mjs`, its Node
tests, and the corresponding frozen authority reference intact and runnable as
executable-reference evidence until independently reviewed Python equivalents
cover every portable contract, state-machine, replay, race, refusal and
restart obligation they currently witness.

No new trusted-host feature is implemented in the Node reference. Python cuts
re-express language-neutral obligations rather than transliterating JavaScript
mechanics. Proxy, accessor, UTF-16 and iterator-specific cases remain evidence
for properties such as inert POD, no caller execution, contract-unit length
and bounded work; Python proves those properties with its own hostile objects,
subclasses, decoded JSON and wide records.

Retirement is a separate, explicit terminal action after Python parity and
independent review. Until then, no cleanup, move or deletion may make a
portable obligation impossible to recover. The final trusted-host acceptance
still requires that production imports and entry points reach only the Python
authority and Worker Manager and never execute the frozen Node tree.

## Keep dependency distributions out of Git — confirmed 2026-08-24

The pending proposal to retain `v12/python/wheelhouse/` is rejected. This also
supersedes only the repository-local/offline-artifact clauses in the runtime
validation ruling above; it does not supersede runtime Draft 2020-12
validation, the `jsonschema==4.26.0` pin, the complete Python 3.13 dependency
closure, or hash verification.

The repository carries `pyproject.toml`, the exact hash-locked
`requirements.lock`, source, tests and package data. It does not carry
downloaded wheels or source distributions from those requirements, including
the platform-specific `rpds-py` wheel. A normal checkout creates its own
disposable venv and downloads the exact permitted artifacts from its configured
package index while enforcing the lock and hashes. Building that environment
is expected setup work for anyone who obtains the repository.

An operator-maintained cache, certified artifact bundle or offline mirror may
later supply the same locked artifacts as deployment infrastructure, but it is
outside the source tree and is not the default fresh-checkout contract. Remove
the local wheelhouse from the W4 deliverable and revise gates that currently
claim repository-local or `--no-index` installation; retain the installed-
layout gate using an environment built from the authoritative lock.

Enforce this boundary in `.gitignore` with the exact
`v12/python/wheelhouse/` directory. The repository already ignores disposable
`.venv/` directories. Do not add a global `*.whl` rule: an exact generated-
artifact directory prevents accidental dependency commits without hiding a
future wheel intentionally retained as a test fixture or durable evidence.

## Independent review of Python Cut A part one — 2026-08-24

**Accepted:** the option-independent package-data, exact-POD and canonical-byte
foundation is correctly separated from the absent validator seam. The schema
copies agree byte-for-byte with both canonical assets and the frozen Node
copies. All 21 Node-generated canonical vectors agree, including the
Python-specific UTF-16 member-ordering hazard. Every delivered test remains
green.

**Observed — changes requested:** ordinary `kind.__name__` dispatch lets a
hostile metaclass execute while the manager is naming a rejected value, so the
call escapes the closed refusal taxonomy. The exported `ERROR_CODES` dict is
the live category/code authority and is mutable, so a caller can open the
supposedly closed pairing. Finally, bounding before `ascii()` lets escaped
astral names and lone-surrogate labels expand 60/160-character inputs into
1,933/1,004-character messages, violating the standing under-500 diagnostic
property.

The three additive regressions are the only failures in a 270-case source run;
the delivered baseline remains 267/267. The now-recorded runtime-validator
ruling also means this partial handoff cannot complete Cut A: pin and provision
`jsonschema==4.26.0` with its full Python 3.13 closure and deliberately migrate
the superseded empty-dependency assertions under items 4bh/4bi. Review:
`review-2026-08-24T09-56-54Z.md`; evidence:
`evidence/review-cutA-part-one-2026-08-24.txt`.

## Independent re-review of complete Python Cut A — 2026-08-24

**Accepted:** all three part-one regressions are closed. Runtime Draft 2020-12
validation is present with the complete hash-locked `jsonschema==4.26.0`
runtime closure, ownership precedes the library, schema-library instance prose
is not retained, the authority module remains standard-library-only, and the
frozen Node oracle remains intact. All 297 delivered source cases are green.

**Observed — changes requested:** `type.__getattribute__` still invokes a
metaclass `__name__` descriptor while naming a rejected type. The supposedly
frozen authoritative `_PAIRING` has a mutable outer dict. Exported
`validate_against` executes an arbitrary caller-supplied validator, while the
two fixed validators retain the same mutable schema dicts exported for
reading, so callers can rewrite runtime validation. Finally, canonicalization
does not enforce the ownership depth/width bounds, allowing refused documents
to acquire durable bytes and digests.

Five additive methods expose these seams. The complete source run is 302
methods with six failures and one error because the canonical-bound method has
three independently failing subtests; the delivered baseline remains 297/297.
Two comments also retain superseded no-validator/empty-dependency claims.

**Proposed repository shape:** retain the 3.2 MB local wheelhouse. The approved
package and gate are self-contained, offline and hash-locked, the prior shared
wheelhouse cannot supply this closure, and no separate reproducible artifact
provisioner exists. This proposal awaits Slawomir's authority; it is not a
review ruling. Review: `review-2026-08-24T10-15-14Z.md`; evidence:
`evidence/re-review-cutA-complete-2026-08-24.txt`.

## Independent re-review of the Cut A correction — 2026-08-24

**Accepted:** the preceding four P1 seams and P2 shared-bound defect are closed
on their default paths. The independently run source and installed gates both
pass all 302 delivered methods, the two stale statements are corrected, and
the frozen Node oracle remains untouched.

**Observed — changes requested:** both exported recursive functions expose the
bookkeeping parameter that enforces the shared rule. A caller can supply a
negative `_depth` to `canonical_text` or `own`, causing a document beyond
`MAX_DEPTH` to canonicalize or become owned successfully. The bound is shared,
but the enforcement state is caller-controlled. Two additive regressions leave
the full source result at 302/304. Review:
`review-2026-08-24T10-24-07Z.md`; evidence:
`evidence/re-review-cutA-correction-2026-08-24.txt`.

## Python Cut A independently signed off — 2026-08-24

The traversal-state correction closes the final reviewed Cut A gap. Exported
`canonical_text` and `own` now accept only genuine operands and initialize
their private recursive helpers themselves. The retained negative-depth cases
are green, and a package-wide public-parameter audit guards the rule against
future bookkeeping parameters regardless of whether their names begin with an
underscore.

Independent source and installed gates both pass 307/307 with the validator
resolved offline from the hash-locked closure. This sign-off covers package
data, exact POD ownership, canonicalization/digests, closed refusals and runtime
Draft 2020-12 validation. W4 remains open for cuts B through F; proceed next to
PLAN item 4bc. The wheelhouse repository-shape ruling remains pending. Review:
`review-2026-08-24T10-28-27Z.md`; evidence:
`evidence/signoff-cutA-traversal-state-2026-08-24.txt`.

## Repository-local wheelhouse rejected — confirmed 2026-08-24

Slawomir rejects retaining downloaded wheels or source distributions in the
repository deliverable. This explicitly supersedes the repository-local and
offline-artifact clauses in the runtime-validator ruling and Cut A review
history; the exact dependency versions, complete Python 3.13 closure and hashes
remain authoritative in `requirements.lock`.

Normal setup creates a disposable environment and downloads only artifacts
whose hashes satisfy that lock from the configured package index. The
installed-layout gate remains required. It no longer uses repository-local
`--no-index`; external caches, mirrors and certified artifact bundles are
deployment concerns rather than source-tree contents. PLAN item 4bp is the
current actionable ruling.

## Independent review of Python Cut B — 2026-08-24

**Accepted:** the separate store ownership marker, transaction/savepoint
discipline, exact result/refusal replay, JSON-null presence distinction, fresh
projections, restart evidence and initialized-store process race are correctly
scoped. All 334 delivered source methods remain green.

**Observed — changes requested:** concurrent first openers all decide the schema
is empty before locking, so the winner initializes and the waiters escape as
`table meta already exists`. A foreign database whose unrelated table is named
`meta` escapes as `no such column: key` instead of the closed refusal. Replay
selects but never compares the stored operation kind, so the same id/signature
argument under a different kind returns the first result. Finally, the journal
schema permits all impossible committed/refused result/refusal combinations
instead of enforcing one sealed outcome.

Four additive methods leave the full source result at 334/338 methods, reported
as five failures and two errors because the row-invariant method has four
failing subtests. Approved item 4bp is also pending implementation. Review:
`review-2026-08-24T10-42-01Z.md`; evidence:
`evidence/review-cutB-control-store-2026-08-24.txt`.

## Independent re-review of the Cut B correction — 2026-08-24

**Accepted:** all four original review findings are closed. The store adopts a
compatible initialization winner, translates an unrelated `meta` shape to the
closed refusal, binds stored kind on first write and replay, and schema version
2 enforces one sealed outcome. Item 4bp's mechanism is also present: no
dependency distributions remain in the repository and the constructed
environment downloads the exact hash-enforced lock.

**Observed — changes requested:** `_agreeing` treats parseable JSON with a
matching `kind` as the manager's canonical signature. It accepts an indented
spelling, a document without `operands`, and a document with an extra member,
then journals identities `manager_signature` cannot produce. The boundary must
require the exact two-member shape and exact canonical bytes before writing.
Two additive methods expose three failures; full source is 348 methods with
three failures and one environment-dependent skip, all 345 others green.

The active gate prose still says the lock resolves offline and that absence of
the removed wheelhouse causes refusal. This is documentation drift from the
confirmed item 4bp ruling even though the implemented download mechanism is
correct. The independent installed attempt could not resolve the configured
index in this managed environment and was not escalated; implementer evidence
records the delivered 346/346 installed run green. Review:
`review-2026-08-24T10-53-27Z.md`; evidence:
`evidence/re-review-cutB-correction-2026-08-24.txt`.

## Independent re-review of the Cut B signature correction — 2026-08-24

**Accepted:** the supplied signature is now owned as an exact two-member POD
document and compared byte-for-byte with its canonical serialization before
replay or a write transaction. Both retained signature methods pass. Active
gate and lock prose now describe the configured-index mechanism rather than the
removed wheelhouse/offline one, and the new current-tree check passes.

**Observed — changes requested:** the separate `kind` operand is still not
proved as durable text. Null escapes through the journal's NOT NULL constraint,
integer 7 commits after SQLite coerces it to text and then collides with its own
exact retry, empty text commits, and a behavior-bearing kind executes its
`__eq__` during the comparison. Exact canonical signature bytes cannot make a
separate unowned SQL operand safe. Validate exact non-empty encodable text before
comparison or SQL, and share the rule with `manager_signature`.

One additive method leaves full source at 350 methods, reported as three
failures, one error and one environment-dependent skip; all 345 other methods
pass. The independent installed attempt again could not resolve the configured
index in this managed environment and was not escalated; implementer evidence
records delivered 349/349 locked. Review:
`review-2026-08-24T11-02-11Z.md`; evidence:
`evidence/re-review-cutB-signature-2026-08-24.txt`.

## Independent re-review of the Cut B durable-text correction — 2026-08-24

**Accepted:** operation kind, operation identities on writes and both reads,
clock answers, and sealed-refusal text now pass one exact non-empty encodable-
text rule before SQL; `manager_signature` shares the kind rule. All retained
and implementer correction cases pass. The exact no-wheelhouse enforcement is
also accepted: only `v12/python/wheelhouse/` is ignored, adjacent wheels and
setup/lock files are not, and no global `*.whl` rule exists.

**Observed — changes requested:** the internal `durable_text` rule was newly
exported without making its diagnostic label a safe public operand. A hostile
label executes `__format__` during refusal, and a 100,000-character label yields
a 100,061-character diagnostic. Keep the helper private or apply the existing
bounded no-code label rule if it is deliberately public.

One conditional additive method leaves full source at 353 methods with one
failure and one environment-dependent skip; all 352 delivered methods pass.
Implementer evidence records 352/352 locked with no skip. Review:
`review-2026-08-24T11-09-02Z.md`; evidence:
`evidence/re-review-cutB-durable-text-2026-08-24.txt`.

## Python Cut B independently signed off — 2026-08-24

The exported-label correction closes the final reviewed Cut B gap. The shared
durable-text rule is private and absent from both exported surfaces, the
retained conditional regression passes, the two named schema validators bound
their own public labels, and the non-vacuous cross-package exported-label audit
passes.

The separate control store, ownership/adoption marker, schema version and row
invariant, transaction/savepoint discipline, exact canonical operation
identity, success/refusal replay, restart and process-race behavior, durable
SQL-text boundary, item 4bp download mechanism, and exact no-wheelhouse ignore
boundary are accepted. Independent source passes 355/355 with one explicit
ambient-version skip; implementer evidence records 355/355 in the locked
environment with none skipped. W4 remains open for Cuts C through F; proceed to
PLAN item 4bd. Review: `review-2026-08-24T11-13-41Z.md`; evidence:
`evidence/signoff-cutB-exported-label-2026-08-24.txt`.

## Independent review of Cut C offers and claims — 2026-08-24

**Accepted:** the narrow injected authority port and injected claim-signature
derivation are accepted decisions. The issue, acceptance, decline, submission,
settlement, late-commit and asymmetric-recovery paths are present with the
expected positive-path boundaries. All 393 delivered methods remain green.

**Observed — changes requested:** the port verifies only that its four session
operations exist, so non-callable capabilities pass construction and fail as a
raw `TypeError` after durable acceptance. Cut C's local text validator accepts
lone surrogates, producing raw SQLite `UnicodeEncodeError` on both an offer-id
read and expiry's clock operand; unrestricted nonempty strings are also treated
as instants, so `"not-an-instant"` lexicographically expires a live offer. A
negative caller-controlled TTL spends entropy and commits an already-expired
authorization. Finally, the offers schema documents an all-five-or-none frozen
acceptance identity but allows both accepted rows with all five fields absent
and issued rows with acceptance timestamps populated.

Five additive methods expose eight assertion failures and two raw errors in a
398-method source inventory plus one explicit ambient-version skip. Require
callable capabilities, shared durable text, exact instant grammar, positive
exact-integer TTL before entropy, and a versioned schema invariant spanning all
five acceptance fields and all offer states. Review:
`review-2026-08-24T11-29-52Z.md`; evidence:
`evidence/review-cutC-offers-and-claims-2026-08-24.txt`.

## Independent re-review of the Cut C correction — 2026-08-24

**Accepted:** every original reviewer method now passes. The port separates its
bound participant from four callable operations, named offer/time inputs use
the shared validators, nonpositive/non-exact-integer TTLs are refused, and
schema version 4 enforces all five frozen acceptance fields across the complete
state partition while refusing earlier versions.

**Observed — changes requested:** the claimed boundary sweep remains partial.
Submit and settlement look up an unproved offer id, and filtered expiry sends an
unproved Work id directly to SQLite; lone surrogates escape from all three as
raw `UnicodeEncodeError`. Profile certification canonicalizes integer kind/name
operands and commits their interpolated key rather than enforcing exact durable
text. A callable injected claim-signature derivation may return `None`, which
reaches the acceptance CHECK as raw `sqlite3.IntegrityError` instead of being
owned as the frozen TEXT identity it becomes. Finally, every positive integer
passes TTL validation: `10 ** 100` performs authority reads and then escapes
from `timedelta` as `OverflowError`.

Four additive methods leave full source at 404 methods with two failures, five
raw errors and one ambient-version skip; all 400 delivered methods remain
otherwise unchanged and implementer evidence records 400/400 locked. Complete
the shared durable-text ownership at all six sites and prove deadline
representability before reads/entropy. Review:
`review-2026-08-24T11-38-34Z.md`; evidence:
`evidence/re-review-cutC-correction-2026-08-24.txt`.

## Independent re-review of the Cut C derived sweep — 2026-08-24

**Accepted:** all nine prior reviewer methods pass. The six durable-text sites
are owned at common boundaries, injected signature output is proved before the
acceptance write, and excessive positive duration is translated before
authority reads. Focused offers pass 47/47 and the exported-callable sweep
passes 3/3.

**Observed — changes requested:** the shared instant rule proves only fixed-
width digits, not a representable calendar instant. The value
`2026-99-99T99:99:99.999Z` passes it, then escapes from `_later` as raw
`ValueError` because parsing occurs outside the handler; in comparison-only
expiry it sorts after a real deadline and silently expires a live offer.
Additionally, the new sweep's `settle_claim` row has no accepted offer and
accepts any `ContractRefusal`: its spoiled `now` case is refused for an absent
offer before clock validation, so removing that validation leaves the claimed
coverage green.

Two additive methods leave full source at 409 methods with one failure, one raw
error and one ambient-version skip; all 407 delivered methods remain otherwise
unchanged and implementer evidence records 407/407 locked. Establish calendar
representability in the shared instant rule and make later-operand sweep rows
reach their named boundary. Review: `review-2026-08-24T11-45-39Z.md`; evidence:
`evidence/re-review-cutC-derived-sweep-2026-08-24.txt`.

### Anti-loop gate applied during that review

PLAN item 4bx arrived while the review was in progress. The surviving
calendar-impossible instant is the same instant/deadline class outside the
claimed inventory, and the settlement-clock row proves that inventory accepts
an earlier precondition refusal without reaching its named operand. The gate is
therefore triggered: Cut D stays unstarted, and Cut C returns the centralized
boundary layer for explicit redesign rather than another named-site correction.
The redesign must derive the public caller-text, SQL-identity, injected-result,
instant and deadline inventory from code and make every probe establish valid
preconditions. Addendum: `review-2026-08-24T11-46-38Z.md`.

## Cut C anti-loop boundary — confirmed 2026-08-24

The 78th W4 message establishes the stop condition. The first Cut C correction
made every original review method pass and claimed a complete SQL/time sweep;
the next review found the same durable-identity and representable-deadline rule
missing at six additional paths. This is no longer accepted as a sequence of
unrelated named-site defects.

The current correction must derive a complete Cut C boundary inventory from the
code, mapping every public operation, caller-supplied or injected identity,
callback result, SQLite lookup/write operand and deadline computation to its
one owning validator. Its tests must fail non-vacuously when an exported
operation or boundary is added without entering that inventory. The reviewer
verifies the inventory and its completeness mechanism rather than checking only
the witnesses named in message 78.

If the next re-review finds another instance of the same durable-text, instant,
deadline-representability or persistent-identity class outside the inventory,
do not request another local substitution. Pause Cut C before Cut D and return
the boundary design for an explicit centralized redesign. A genuinely new,
unrelated defect remains ordinary review work; this stop condition is for the
repeated class that the claimed sweep was supposed to close.

## Validate once at each receiving trust boundary — confirmed 2026-08-24

The centralized redesign validates data once when it enters a trust domain.
Every caller-supplied value, persisted value being adopted, and result returned
by an injected, callback, adapter, agent or remote component is input to the
receiving component and must be owned under the accepted rule before trusted
processing, persistence, comparison, entropy or authority mutation. What one
component calls output is therefore validated as input by its receiver.

Do not blanket-revalidate every internal function return. After admission, the
trusted core works with owned internal values and preserves their invariants.
Outbound contract documents are produced through closed, contract-aware
canonical constructors so malformed wire state is not an ordinary internal
possibility; the receiver still owns the document at its own boundary. This
separates one real boundary check from both under-validation and repeated
defensive checks scattered throughout the core.

The Cut C inventory must identify the trust-domain entry and owning validator,
not merely every function that happens to touch the value later. Its callback-
result rows are receiving-input rows, not a general requirement to validate all
outputs.

## Independent review of the centralized Cut C boundary layer — 2026-08-24

**Accepted:** the centralized instant owner establishes text, frozen grammar
and a real calendar instant. All eleven prior reviewer methods pass, and exact
boundary labels make the old earlier-refusal vacuity observable.

**Observed — anti-loop redesign remains required:** the derived inventory starts
from existing boundary-validator calls rather than independently enumerating
receiving trust entries. It therefore cannot find an input that has no
validator. It also omits exports with empty reached sets, collapses class
methods and repeated `(kind, label)` call sites, and checks only the global
union. AuthorityPort, claim_operation_id and revive_refusal are already absent
without failing the delivered gate.

The omission is live in both trust domains PLAN 4bz named. Malformed adopted
journal result/refusal payloads escape as JSONDecodeError and KeyError. Integer
project_work output faults at `.get`; integer claim output is persisted and
advances the offer to claimed; integer settlement output is silently treated as
live. Six additive methods leave full source at 423 methods with three failures,
three raw errors and one ambient-version skip; all 417 delivered methods remain
otherwise unchanged and implementer evidence records 417/417 locked.

Cut D stays unstarted. Derive the inventory from public caller entries,
persistent adoption/decodes and injected/callback results independently of
validators, then map each source entry to one closed owner and one reachable
probe. Review: `review-2026-08-24T11-58-38Z.md`; evidence:
`evidence/review-cutC-central-boundary-layer-2026-08-24.txt`.

## Independent review of the trust-domain correction — 2026-08-24

**Accepted:** the six preceding persistent-journal and broad injected-result
witnesses now pass, as do all 425 delivered methods. The port refuses values
that are not documents and settlement discriminators outside its vocabulary;
persisted journal JSON faults are translated at adoption.

**Observed — changes requested:** adopted inventory discovery still starts with
existing `boundaries.adopted` calls. It therefore omits an SQL offer row whose
fields are returned by `_offer_row` without adoption; a malformed persisted
settlement deadline reaches comparison and is accepted while the inventory is
green. The new `document` owner accepts extra members, and `alternative` closes
only the kind vocabulary rather than each variant's required/optional members.
Consequently an extra Work-projection member is accepted and a committed answer
without a result advances the offer to claimed with a null assignment.

The probe gate also remains the old global `(kind, label)` sweep and never maps
each `(domain, owner, entry)` row to its own reachable probe. Complete the
independently derived lexical entry/owner/probe model and 4bz's separately
acknowledged closed outbound constructors before re-review; do not patch the
three witness sites locally. Three additive methods leave full source at 428
methods with three failures and one ambient-version skip; every delivered method
otherwise passes. Cut D remains unstarted. Review:
`review-2026-08-24T12-14-23Z.md`; evidence:
`evidence/review-w4-trust-domains-4bz-2026-08-24.txt`.

## Independent review of closed shapes and outbound constructors — 2026-08-24

**Accepted:** exact member and variant sets, SQL-derived adopted rows and the
outbound constructor routing are present. The three preceding reviewer
regressions pass, and all 455 delivered methods are green at source.

**Observed — anti-loop redesign remains required:** the receiving universe
still omits entire input forms. It walks ordinary parameters but not variadic
parameters, capability calls but not injected attribute values, and explicitly
removes caller-supplied capability objects whether or not construction owns
them. A session with an unencodable bound participant constructs; a non-callable
bearer mint performs authority reads before raw TypeError; nine public
`**members` constructors do not exist in the claimed every-parameter universe.

Exact POD and an exact member set are also not the semantic member contract. An
integer projection authority_uuid is accepted and issued, a claim answer naming
another participant is recorded, and a text generation reaches SQLite and
escapes as raw IntegrityError after the authority answer. The entry model must
represent the identity/type/relationship rules of fields the manager persists
or branches on, not only their container.

Finally, `_operation_row` owns and JSON-checks a persisted refusal, after which
replay routes it through public `revive_refusal` and adopts/owns the same value
again. Preserve direct-call ownership and give already-owned replay an internal
trusted decoder instead. Six additive methods leave full source at 461 methods
with 13 failure reports, two raw errors and one ambient-version skip; every
delivered method otherwise passes. Cut D remains unstarted. Review:
`review-2026-08-24T12-46-50Z.md`; evidence:
`evidence/review-w4-closed-shapes-outbound-2026-08-24.txt`.

## Independent review of semantic field relationships — 2026-08-24

**Accepted:** all four Python signature forms, the bound participant entry,
capability-operand typing, shared claim/committed assignment ownership and the
split trusted refusal decoder are present. The preceding six reviewer
regressions pass, and the 51-method inventory gate is green.

**Observed — anti-loop redesign remains required:** the assignment owner types
the returned authority UUID but never relates it to the authority frozen on the
offer. A direct claim and a late committed claim from another authority both
advance the offer to claimed and record the foreign generation. The four-part
assignment identity therefore still has an unowned relationship.

The structural universe also stops short of semantic nested fields. It sees a
retirement's `record` but not the `reason` and `disposition` read after a boolean
alias; integer reason is accepted and durably settles the offer. On the adopted
side it treats the operations table as one entry and the refusal contract as a
tuple of member names. Integer `category` therefore passes the row owner and
escapes replay as AssertionError from the refusal constructor. The same class
the previous review returned — exact POD/member presence without semantic field
ownership — survives while the completeness gate is green.

Four additive methods leave full source at 477 methods with four failures and
one ambient-version skip; all failures are the new witnesses. Apply the 4bx/4by
anti-loop gate: extend the centralized injected/adopted entry model and its
shared owners rather than patching named sites, and keep Cut D unstarted.
Review: `review-2026-08-24T13-14-01Z.md`; evidence:
`evidence/review-w4-semantic-field-relations-2026-08-24.txt`.

## Independent review of sealed-refusal ownership — 2026-08-24

**Accepted:** direct and late-commit assignments now relate their authority to
the offer, retirement fields are typed, and the preceding four reviewer
regressions pass. Adopted consumed columns are represented in the inventory.

**Observed — anti-loop redesign remains required:** the new persisted-refusal
owner reads exported mutable `ERROR_CODES` as authority for the closed pair.
The contracts layer already proves callers can widen that readable vocabulary
without widening its private enforced pairing; doing so lets an invented seal
pass row adoption and then escape replay as AssertionError. A list category
also escapes as TypeError because mapping membership runs before the category's
type is owned.

The public `revive_refusal` path still checks only the exact member set. It
escapes on invalid category/pair, accepts integer message and rewrites a false
durable marker to true. The structural universe contains the caller parameter
`sealed` but none of its semantic fields, so its 54 methods remain green. Three
additive methods leave full source at 483 methods with four subtest failures,
two raw errors and one ambient-version skip.

Give sealed refusals one closed semantic owner that does not depend on a
caller-mutable vocabulary, and extend the caller-domain inventory to structured
semantic fields. Apply it once on public input and once on adopted input while
keeping `_revived` trusted. Cut D remains unstarted. Review:
`review-2026-08-24T13-34-30Z.md`; evidence:
`evidence/review-w4-sealed-refusal-owners-2026-08-24.txt`.

## Independent signoff of one seal owner and caller fields — 2026-08-24

PLAN 4cj is accepted with no remaining finding in the correction slice. The
closed-pair question now types before consulting the private frozen pairing and
exposes no mutable authority. One semantic seal owner is applied once at public
revival and once at adopted replay; trusted revival remains separate. Caller
parameters seed semantic member discovery, so the public seal's category, code
and message are entries with individual probes, while the durable marker is
owned and driven wholly inside the shared boundary without a decorative read.

All three preceding reviewer methods pass. Focused seal plus inventory is
57/57; full source is 483/483 with one retained ambient-version skip. The
independent locked gate repeated the green source stage but could not reach the
configured package index to fetch `jsonschema==4.26.0`. The repository
deliberately has no offline wheelhouse and non-interactive policy forbids an
alternate or escalated path, so this signoff does not claim an independent
locked-build pass; implementer evidence records one in its environment. Cut D
may now begin. Review: `review-2026-08-24T13-47-05Z.md`; evidence:
`evidence/signoff-w4-one-seal-owner-2026-08-24.txt`.

## Independent review of Cut D attempt axes — 2026-08-24

**Accepted:** all eight attempt operands ride the operation signature;
activation relates the session, this attempt's claim and the authority's live
four-part assignment; assignment columns are all-or-none; transition maps are
frozen per axis; and source identity is resolved before current observation
state. Failed inserts roll their axis move back. Keep the activation UPDATE's
compare-and-swap: its present public race is masked by one operation identity,
but that does not make the write condition redundant.

**Observed — changes requested:** a sequential exact activation retry bypasses
the operation journal through the already-fixed shortcut and returns
`already_fixed=True`, while the first committed result and a racing retry both
return `False`. The same operation therefore has timing-dependent answers
instead of one byte-stable result. Observation's axis and value membership
checks also run before typing, so list values escape as raw TypeError despite
the inventory's claimed closed owners. Finally, a deterministic stale
multi-manager observation snapshot escapes as raw `sqlite3.OperationalError:
database is locked`; the frozen host's contention-only, result-code-based
translation was not ported.

Three additive methods leave full source at 517 methods with two failures, two
subtest errors and one retained ambient-version skip; all 514 delivered methods
pass. Retain the regressions and correct the shared retry, vocabulary and
contention boundaries while leaving non-contention storage faults raw. Runtime
start, reconciliation and cancellation remain unstarted. Review:
`review-2026-08-24T15-19-08Z.md`; evidence:
`evidence/review-cut-d-attempt-axes-2026-08-24.txt`.

## Independent signoff of Cut D replay, types and contention — 2026-08-24

PLAN 4cn is accepted with no remaining finding in the correction slice. An
exact activation retry now consults its byte-stable journal result before the
already-fixed fallback, while a four-part mismatch retains the diagnostic that
names the violated attempt precondition. The activation UPDATE's defensive
compare-and-swap remains; its losing branch is a measured equivalence through
today's public operation identity, not a redundant write condition.

Axis and value are typed before their closed membership questions. Observation
contention is classified only from SQLite's primary BUSY/LOCKED result codes,
including masked extended results. A trigger constraint whose prose says busy
and database is locked remains a raw constraint failure, proving application
wording cannot choose a portable retry policy.

All focused cases pass. Full source is 518/518 with one retained ambient-version
skip. The independent locked gate repeated that green source stage but could
not reach the configured index for `jsonschema==4.26.0`; no escalation or
alternate wheelhouse is authorized, so this signoff does not claim an
independent locked-build pass. Implementer evidence records one in its
environment. Runtime start, reconciliation and cancellation may begin. Review:
`review-2026-08-24T15-48-04Z.md`; evidence:
`evidence/signoff-cut-d-replay-types-contention-2026-08-24.txt`.

## Independent review of Cut D runtime and cancellation durability — 2026-08-24

**Accepted:** runtime start is journalled before the adapter call; full labels
include participant; a minted mismatch is checked before filtering;
multiplicity and mismatch cancel; runtime identity is fixed; and cancellation
orders authority, provider agent and runtime while retaining both downstream
failures. The nested cancellation answer and narrowed attach-race catch are
sound departures from the frozen host.

**Observed — changes requested:** `_attach` commits the fixed runtime and
journal result, then records `execution_runtime=running` outside that atomic
act. A fault in the gap followed by a real store reopen replays `attached`
without rerunning the action and leaves the axis permanently
`start-requested`. The observation savepoint is already designed to nest in a
journalled action; make the attachment, observation and result one committed
act or provide equivalent atomic semantics.

`AuthorityPort.cancel` also owns and relates only three parts of the returned
fenced assignment. It shapes generation but never compares it with the exact
generation in `expect`, so a fence for generation 2 authorizes agent cancel and
runtime stop for an attempt fixed to generation 1. Relate all four assignment
parts before either downstream boundary runs.

Two additive methods leave full source at 543 methods with two failures and one
retained ambient-version skip; all 541 delivered methods pass. Retain both
witnesses and keep output, intake and cleanup unstarted until this correction
is reviewed. Review: `review-2026-08-24T16-47-16Z.md`; evidence:
`evidence/review-w4-runtime-cancellation-durability-2026-08-24.txt`.

## Independent signoff of atomic attachment and exact fence — 2026-08-24

PLAN 4cr is accepted. The running observation now executes inside the
attachment's journalled transaction, so a fault rolls back runtime identity,
observation and operation result together. The retained witness proves that
nothing partial commits and that one retry after a real store reopen performs
the complete attachment and reaches `running`.

The implementer's two assertion changes are approved: they express the atomic
remedy the preceding review recommended, rather than its permitted alternative
of repairing a committed partial act. The reviewer renamed the test because
“committed replay repairs” no longer described the accepted mechanism; no
assertion or behavior changed in that cleanup.

The returned fence assignment is also compared with the exact expected
four-part identity before either downstream cancellation call. A different
generation refuses and orders nothing. Focused correction cases pass 2/2; full
source is 543/543 with one retained ambient-version skip. The independent locked
attempt could not resolve the pinned validator because the configured index
hostname was unavailable, so this signoff does not claim an independent locked
pass; implementer evidence records one. Output, intake and cleanup may proceed.
Review: `review-2026-08-24T17-06-21Z.md`; evidence:
`evidence/signoff-w4-atomic-attach-exact-fence-2026-08-24.txt`.

## Independent signoff of named manifest fragments and digest identity — 2026-08-24

PLAN 4ct is accepted. Both requested design decisions are now ruled. The public
fragment boundary accepts one name from the frozen schema's `$defs`, never a
caller-supplied subschema: schema data is executable validation policy, and
every validator this package runs must be package-built and identity-owned.
Each fragment validator contains exactly the frozen `$schema`, `$id`, `$defs`
and its selected `$ref`; carrying the root envelope's `oneOf` would wrongly
require a fragment to validate as an envelope too.

The definition types before membership, documents are exact-POD owned before
the library walks them, and the validators share the private frozen parse.
Digest verification owns the manifest, requires the declared identity,
recomputes over every other member and returns the computed value. The exact
canonical input-manifest vector passes both helpers.

This is accepted as groundwork because its names and plan do not claim the full
manifest trust entry. The remaining §12 semantic rules, retention, tables and
freeze/record remain explicitly queued. Focused tests pass 22/22; full source is
555/555 with one retained skip. The independent locked attempt could not resolve
the pinned validator because the configured index hostname was unavailable;
implementer evidence records the locked pass. Review:
`review-2026-08-24T17-42-45Z.md`; evidence:
`evidence/signoff-w4-manifest-fragment-digest-2026-08-24.txt`.

## Independent review of §12 manifest semantic boundaries — 2026-08-24

**Accepted:** schema-before-semantics, digest identity, Work authority-prefix
relation, recursive artifact/content discovery, bytewise content ordering and
aggregates, input name/destination/object-namespace rules, canonical-vector
resealing, and the two schema-owned deletion decisions are sound. The composite
also correctly withholds the whole trust-entry name while §13 is absent.

**Observed — changes requested:** the frozen URI boundary constructs a URL and
rejects userinfo, while Python calls permissive `urlsplit` and discards its
result. Credential-bearing userinfo is accepted, as are authorities with a
space or a nonnumeric port that the frozen parser refuses. Keep the
original-text query/fragment checks, but own userinfo and the authority/port
syntax that splitting does not validate.

`check_work_ref` and `check_content_manifest` are also exported in the package's
promised surface but index caller operands without shape ownership. Malformed
values escape as raw TypeError/KeyError and dict subclasses execute hostile
`__getitem__`. Give the public functions schema-owning wrappers and use private
trusted semantic bodies from the already-owned composite path, avoiding both an
open direct boundary and duplicate validation.

Four additive methods leave full source at 571 methods with five failure
reports, eight raw errors and one retained ambient-version skip; all 567
delivered methods pass. Retain the regressions and correct both boundaries
before §13 or retention. Review: `review-2026-08-24T18-32-54Z.md`; evidence:
`evidence/review-w4-manifest-semantics-boundaries-2026-08-24.txt`.

## Correction review of URI parsing and exported owners — 2026-08-24

**Accepted:** the two exported semantic helpers now schema-own direct caller
values, while the already-owned composite calls private semantic bodies and
does not validate nested documents twice. The structural witness pins that
division. Userinfo in either form, authority characters outside the RFC 3986
alphabet and a nonnumeric port are refused from the parsed result.

**Observed — one P1 remains:** an empty authority still bypasses every parsed-
authority check. Python's `urlsplit("https://")` returns an empty netloc and
`check_uri` accepts the original text, while the frozen host's `new
URL("https://")` raises `TypeError`. A durable locator must not cross this
boundary under parser disagreement. Retain the additive case and make the
Python rule refuse this parser-incomplete absolute locator before §13 or
retention starts.

**Review decision:** extend the anti-loop inventory to the contracts package as
a separate explicit slice after this URI correction and before §13. The current
manager-only inventory could not see these exported contract boundaries or the
accidental double-validation shape caught in review. Derive the contracts
surface from the package's actual public exports, name each semantic owner and
probe, and structurally forbid a composite from re-entering a public owning
wrapper for a value it already owns. This is a prevention gate, not a reason to
broaden the present correction.

Focused correction review passes five of six methods. Full source runs 573
tests with the one new `https://` failure and one retained skip; all delivered
tests pass. Review: `review-2026-08-24T19-04-46Z.md`; evidence:
`evidence/review-w4-uri-correction-2026-08-24.txt`.

## Re-review of the empty-authority correction — 2026-08-24

**Accepted:** the correction now refuses `https://`, `http://` and `ftp://`
without applying a blanket empty-authority prohibition to opaque or `file`
schemes. The previous additive `https://` witness passes.

**Observed — P1 remains:** `_HOST_REQUIRED` asks `urlsplit` whether a special-
scheme URI has a host, but that is precisely where the two parsers disagree.
The frozen WHATWG constructor accepts `https:x`, `https:/x` and `https:///x`,
normalizing every one to host `x`; Python reports an empty `netloc`, and the new
guard refuses all three. The same constructor parses `worker` as userinfo in
the corresponding `https:worker@example.test` forms, while Python refuses them
for “no host” before owning the credential boundary. The measured list of
schemes is sound, but a WHATWG host decision cannot be derived directly from a
`urlsplit` field.

Two additive methods pin both sides: accept the three shorthand host forms,
and still reject their userinfo variants for the credential reason. Full
source is 576 tests with three errors, three failure reports and one retained
skip, all in these new witnesses; every delivered method passes. Retain them
and preserve the fixed `https://` refusal. The contracts-package inventory,
§13 and retention remain unstarted. Review:
`review-2026-08-24T19-25-16Z.md`; evidence:
`evidence/review-w4-special-scheme-host-2026-08-24.txt`.

## Re-review of the derived WHATWG authority — 2026-08-24

**Accepted:** the retained shorthand host forms now agree with the frozen
constructor, and their credential variants reach the userinfo refusal. The
last-colon correction also rejects the measured multi-colon port forms.

**Observed — P1 remains:** the new derived-authority code is still a splitter,
not a parser. `_AUTHORITY` proves only a broad character alphabet and the port
rule proves only decimal characters. It therefore accepts `https:x:65536`,
`artifact://x:65536`, invalid bracket hosts such as `https:[gg]`, unmatched
brackets and the invalid escape `https:%ZZ`, all of which the frozen constructor
refuses. Conversely it rejects the empty port marker on `https:x:`,
`https://x:` and `artifact://x:`, which that constructor accepts and removes.
The prior validated `split.port` access was replaced for ordinary authorities
too, widening that already-correct path.

Two additive methods leave full source at 582 tests with six failure reports,
three errors and one retained skip, all in the new witnesses; every delivered
test passes. This is the third correction on one parser-equivalence boundary.
Do not continue by copying another selected WHATWG clause. Pin a durable parser
strategy first: either a vetted WHATWG implementation owns the same accepted
surface as the frozen constructor, or both runtimes explicitly narrow to one
canonical URI subset under a recorded supersession. The contracts inventory,
§13 and retention remain unstarted. Review:
`review-2026-08-24T20-03-48Z.md`; evidence:
`evidence/review-w4-derived-authority-is-not-a-parser-2026-08-24.txt`.

## Confirmed decision — one smaller canonical URI grammar — 2026-08-24

**Confirmed:** v12 will not reproduce the frozen JavaScript constructor's full
WHATWG acceptance surface in Python. Both retained runtimes instead enforce one
smaller, shared, versioned URI grammar. This explicitly supersedes the earlier
4d/4da/4db requirement to preserve every frozen-host acceptance case; it does
not supersede the retained refusals for credentials, queries, fragments or
malformed authorities.

The worker-control 1.0 subset is deliberately hierarchical and transport
neutral:

- the scheme is lower-case ASCII matching `[a-z][a-z0-9+.-]*`;
- non-file locators use `scheme://authority` followed by either no path or an
  absolute path; `file` locators use `file:///absolute-path` and no remote
  authority;
- a non-file authority contains no userinfo and has one nonempty lower-case
  ASCII DNS/IPv4 host or one bracketed IPv6 literal, plus an optional decimal
  port in the inclusive range 1 through 65535;
- empty ports, malformed brackets, backslashes, control/space characters,
  queries, fragments and invalid percent escapes are refused; and
- path percent escapes, when present, use upper-case hexadecimal. Shared
  positive and negative vectors are the authority for both implementations.

This admits the forms v12 needs now, including `artifact://store/item`,
`https://host/path`, `ssh://host/repo` and `file:///absolute/path`. It
deliberately excludes special-scheme shorthand such as `https:x`, opaque forms
such as `urn:x` and `mailto:x`, empty non-file authorities, empty port markers
and the rest of WHATWG normalization. Adding another form later is a versioned
contract change, not an ad hoc parser exception. The frozen Node implementation
may receive only the bounded correction needed to enforce these shared vectors;
its broader retention as the parity oracle remains in force.

## Independent review of the shared canonical locator grammar — 2026-08-24

**Accepted:** the strategy ruling is implemented over original text in both
runtimes; opaque and shorthand forms are gone; scheme, authority shape,
userinfo, query, fragment, backslash, path character/escape and port rules are
shared through one vector file. The authorized retained-test migrations are
fully named. The bounded Node edit does not touch the unrelated refusal-length
failures already owned by W1593/W2929.

**Observed — changes requested:** Python's `_check_ipv6` claims the same-text
canonical check but only lowercases and calls `IPv6Address`. It accepts
`[2001:0db8::1]`, the uncompressed `[2001:db8:0:0:0:0:0:1]` and scoped
`[fe80::1%eth0]`; Node refuses all three through its character restriction and
constructor round-trip. Python must restrict the literal alphabet and compare
the standard library's canonical rendering with the original literal.

Both runtimes also call the `_DNS`/`URI_DNS` label pattern a DNS host while
omitting DNS's 63-byte label bound. A 64-character ASCII label is accepted by
both even though it is not a DNS host. Enforce the per-label bound and the
overall DNS host bound consistently.

Four additive refused vectors make the common corpus 20 accepted and 54
refused. Full Python remains 574 tests with four additive failure reports and
one retained skip; every delivered test passes. The focused Node contracts file
passes 56 and fails only the new overlong-label vector; its three new IPv6
vectors already pass. Review: `review-2026-08-24T21-42-03Z.md`; evidence:
`evidence/review-w4-canonical-locator-ipv6-dns-2026-08-24.txt`.

## Technical re-review of locator bounds; one ruling remains — 2026-08-24

**Accepted technically:** Python now restricts the IPv6 literal alphabet and
requires its standard library's canonical text; both runtimes enforce 63-byte
labels and a 253-character DNS name. The 58 refused and 20 accepted shared
vectors pass in both focused suites. Python source is 577/577 with one retained
skip; the focused Node contracts file is 60/60.

**Open decision:** the implementation excludes every IPv4-mapped IPv6 address.
The evidence is persuasive: Python canonically writes the mapped range with a
dotted tail while Node canonically writes the same addresses as hexadecimal,
and each normalizes the other's spelling. No original text satisfies both
same-text checks. But the confirmed grammar admitted “one bracketed IPv6
literal”; excluding an address family is a product-contract narrowing, not a
reviewer-owned implementation detail. Approver confirmation is required before
the new four mapped-family refusal vectors and exclusion become authoritative.

The reported 1,532/10,162 differential sweep is supplementary; no durable
reproduction script was supplied, so this review does not independently attest
those counts. Direct examples, shared vectors, source inspection and focused
tests establish the decision boundary without them. Review:
`review-2026-08-24T22-00-43Z.md`; evidence:
`evidence/review-w4-locator-bounds-ruling-2026-08-24.txt`.

## Confirmed clarification — IPv4-mapped IPv6 is excluded — 2026-08-24

**Confirmed:** the shared canonical locator grammar excludes the complete
IPv4-mapped IPv6 range, `::ffff:0:0/96`. Python and Node have incompatible
canonical text for this family, so admitting it would violate the confirmed
cross-runtime same-text rule. The exclusion narrows the earlier phrase “one
bracketed IPv6 literal”; every other recorded grammar clause remains in force.

Any future admission of the mapped family requires a versioned grammar change,
not an implementation-local spelling exception. With that final boundary
approved, the implementation and common vectors satisfy W4. Terminal review:
`review-2026-08-24T22-08-19Z.md`; evidence:
`evidence/review-w4-terminal-signoff-2026-08-24.txt`.
