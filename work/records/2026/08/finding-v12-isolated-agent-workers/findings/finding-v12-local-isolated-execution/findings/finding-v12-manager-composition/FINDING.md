# Finding: the Python manager has no public composition, so nothing consumes a client capability

Canonical Baton Work: W6592 (`2b077949-W6592`), an M2 Job contained by W3
(`V12 M2: Prove local isolated execution`). Created 2026-08-24 by
`baton.claude` on claiming the Job, because this slice produces durable
implementation evidence and the assignment says to create a dossier when it
does.

## What this Job is

The decomposition ruling — umbrella `PLAN.md` item 20, confirmed 2026-08-24 —
required the contracts inventory, §13 and retention to become separate,
independently reviewable Jobs once W4 finished its canonical-locator
correction. W4 finished it. This is the first of those Jobs, and the assignment
names two deliverables:

1. **Inventory the remaining Python Worker Manager receiving boundaries.**
2. **Expose the real public composition path, including the ACP
   client-capability consumer — and do not build a test-only API.**

W641's canonical wire/durable capability shape is preserved rather than
reconsidered. §13 and retention stay out.

## Revalidated on the current tree before acting, not taken from the brief

- **Umbrella PLAN item 20** says exactly what the assignment says it says: give
  every planned cut its own claim, evidence and review cycle, and order the
  contracts inventory, §13 and retention as separate M2 Jobs.
- **W1593 PLAN item 15** and `review-2026-08-24T22-32-23Z.md`: the bounded
  exact-record diagnostic is **signed off as a primitive** and W1593 is blocked
  on this Job only for *black-box acceptance through the actual caller-local
  refusal pair*. It must not reopen the primitive and must not invent a
  test-only public API. So what this Job owes W1593 is a real consumer, not a
  hook.
- **The gap is real.** `clientCapabilities` occurs in
  `src/baton_v12/contracts/schema/agent-session-1.0.schema.json` and **nowhere
  else in the Python source or tests**. The manager package's own docstring
  says the public composition is "still absent rather than stubbed".
- **The certification that exists is a digest with no document.**
  `certify_profile(store, kind, name, profile_digest)` records that a digest is
  certified. Nothing in Python ever sees the profile that digest names, so
  there is no boundary at which `client_capabilities` could arrive — which is
  why the consumer is missing rather than merely unexported.

## The frozen reference this ports from

`v12/src/worker_manager/agent_profile.mjs` and `agent_handshake.mjs`, whose
pinned acceptance is one sentence whose ORDER is the content:

> the core certifies one exact profile by composing shape, document seal and
> policy checks IN THAT ORDER

and whose §2.2 capability rule is **exact rather than "no dangerous member"**,
because a subset check asks whether what is here is safe when the rule is that
nothing may be here — a member ACP adds next version would pass a subset check
on the day it appeared.

W641's ruling is preserved verbatim in intent: **one representation**, and it is
ACP's. `{ "fs": {}, "terminal": false }` on the wire and the same structural
document persisted. Absence is how withholding is expressed; Baton does not
synthesize an explicit `false` to restate it. A provider-neutral capability
model, if one is ever needed, is separately justified Work with its own
versioned contract and not a translation invented at this boundary.

## Ownership

The Python manager and contracts packages are W4's implementation, and W4 is
closed. This Job owns the composition modules it adds and the tests that go with
them. It does not reopen W1593's primitive, does not touch the frozen Node
reference, and does not start §13 or retention.

## 2026-08-24 independent review of cut A

**Observed [P1]:** Python's equality relation silently widens the frozen
wire-version rule. `negotiate_acp` compares the caller's answer to the integer
pin with `!=`; consequently `True` is accepted as ACP version `1`. The frozen
reference uses JavaScript's type-strict `!==`, so this is not a permitted port
difference. The exact match must distinguish a Boolean from an integer before
constructing the negotiated document.

**Observed [P1]:** `_offered` owns arbitrary JSON and then iterates it; it does
not own the exact built-in list the new receiving-boundary inventory says it
owns. A record whose six keys are the required capabilities passes as though it
were the list. A real list containing all six plus `1`, `true`, or `null` also
passes because `_offered` silently drops the extra non-text member. The public
boundary must establish one exact built-in list and text members before using
them as capability names; owning a broader JSON value and projecting a subset
is not the same contract.

Additive review cases in `tests/manager/test_handshake.py` demonstrate both
failures. The focused 31-case module has five failing subcases: one Boolean
wire answer, one record answer, and three non-text JSON members. Cut A is
changes-requested; cut B remains deliberately unstarted until this review is
resolved.

Operationally, this dossier existed without W6592's required canonical Baton
binding when review began. The reviewer repaired the binding to this permanent
record before executing the review.

## 2026-08-24 decomposition correction

**Confirmed by M6776:** the two independently reviewable deliverables require
two Work identities, not two rounds inside W6592. W6592 is narrowed to Cut A,
the public manager composition. The contracts-package receiving inventory is
superseded here and moves to a separate W3-contained Job and dossier. References
above to Cut B describe the original decomposition history; they are not a live
instruction to continue it under this claim.

## 2026-08-25 independent re-review of corrected cut A

**Confirmed:** both previously reported exact-type gaps are corrected. A
Boolean no longer satisfies the integer wire pin, and the capability answer is
now established as one exact built-in list containing only text. The original
31-case handshake module passes before the new re-review regression is added.

**Observed [P1]:** the derived certification operation identity mistakes a
historical journal result for a current certification. Certifying profile bytes
A, replacing them with bytes B under the same `profile_id`, then asking to
certify A again returns A's earlier successful result without running the
upsert. `certified_agent_session_profile(A)` consequently still returns
absence. The public operation says it certified a document that the store does
not currently certify.

The additive
`test_recertifying_prior_bytes_makes_them_current_again` in
`tests/manager/test_handshake.py` demonstrates the failure. The focused module
is 32 cases with exactly that one failure. A historical effectively-once
result may remain history, but it cannot stand in for a state-setting effect
that a later operation replaced.

**Observed [P2]:** `handshake.py`'s module contract still says the §2.2 check is
reached from the certification path. The implemented and recorded superseding
decision places it at emission in `negotiate_acp`. The public module narrative
must name the one live rule rather than preserving both placements as though
both were current.

## 2026-08-25 final independent re-review

**Confirmed satisfying for W6592 Cut A.** Certification now performs its
idempotent state-setting upsert on every call rather than replaying a historical
journal result whose effect may have been replaced. The A → B → A regression
passes and lookup returns A as current after the third call. The module
narrative now consistently places §2.2 at emission.

The complete focused handshake module is 32/32. The shared boundary inventory
has no W6592 failure: its current failures are the separately recorded
W6631/W6632 declaration gaps plus one in-flight W7079 expectation changed by
that constructor Work. Those do not reopen this cut's composition, profile,
wire-version, capability, or retained-row boundaries.

Signoff: `review-2026-08-25T00-28-14Z.md`.
