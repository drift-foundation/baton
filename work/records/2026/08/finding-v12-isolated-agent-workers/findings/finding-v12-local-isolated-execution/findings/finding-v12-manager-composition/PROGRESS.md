# Implementer progress — the Python manager's public composition

Created 2026-08-24 by `baton.claude` on claiming W6592.

## Cut A — one certified profile, and the capability it advertises

The gap was not that the consumer was unexported. `certify_profile` recorded
that a **digest** was certified, and nothing in Python ever saw the document
that digest named — so `client_capabilities` had nowhere to arrive and §2.2 had
nothing to enforce. Cut A gives the document a door.

`handshake.py` composes **shape, then the document seal, then policy**, in that
order and for the frozen module's stated reasons. The store gains a `profiles`
table holding the exact canonical **bytes** rather than the digest alone,
because a session must pin the per-posture policy a profile carries and a digest
cannot be read for it. Reading one back requires **all three witnesses** — what
the document declares, what its bytes recompute to, and the key it is filed
under — since two of three agreeing is not agreement.

W641's ruling is preserved: one representation, and it is ACP's.

### The finding this cut produced: §2.2 was in the wrong place

I first put `check_client_capabilities` on the certification path, which reads
naturally — the document arrives there. Then I measured it. **For a
profile-carried document the frozen schema states §2.2 exactly**:
`clientCapabilities` requires `fs` and `terminal`, admits no other member, makes
`fs` an empty closed object and pins `terminal` to the constant `false`, and the
ACP conditional makes it non-null. Every document the rule refuses, the schema
refuses first — checked, not assumed.

So a capability check *after* the schema has spoken is the second live source of
truth this schema's own prose warns about: "two live sources of truth is how a
certified profile comes to disagree with the policy actually enforced."

The rule belongs where it is **not** implied — at **emission**. The schema
constrains what may be *stored*; §2.2 constrains what is *sent*, and W641's
correction was about exactly that difference: the host had one constant standing
for two documents and emitted the durable summary onto the transport, sending
field names ACP does not have. So `negotiate_acp` sends
`check_client_capabilities(profile["client_capabilities"])` — the profile's own
document, passed through the rule — rather than answering from a module
constant, which would restore the seam where the profile says one thing and the
wire carries another with nothing comparing them.

`ACP_CLIENT_CAPABILITIES` is a read-only mapping for a related reason: a
module-level document would be one object every caller could edit, and a
*function* returning a fresh copy would put a constant on the callable surface,
where every sweep over the exported operations has to explain why one of them is
not an operation.

### What the boundary inventory made me do

Adding a module to this package is not a matter of adding a module. The
inventory found, in order:

- an owner whose label was a **variable**, which it cannot attribute — three
  sites, all fixed to literals;
- eight caller entries with **no owner**, of which two were parameters I had
  ported but never read (`what`, `agent_methods`). An operand supplied and
  ignored is one the caller believes it chose, so both are gone rather than
  declared;
- sixteen owned entries with **no probe** — each now has one that spoils
  exactly its own member;
- a stated owner with **no witness** — three witness cases added;
- and the agent's capability answer walked **unowned**, which a generator
  yielding the six capabilities once would have passed a handshake with and then
  failed every one of.

The store's object inventory, the declared-operand vocabulary and the
unstorable-text sweep each needed this cut's entries too. All three are
completeness checks, and all three caught it.

## Mutation — 16 of 16 killed, and three survivors that each said something

The first round killed 13. The three survivors were not one kind of gap:

- **H16, "the wire document is shared rather than fresh"** — a shallow copy of
  the read-only constant left `fs` as the mapping proxy itself, and every case
  still passed. That is a real defect: a document carrying a proxy is not one a
  consumer can canonicalize, own or store. A case now asserts the emitted
  answer is plain built-in data all the way down, and survives `own`.
- **H11, "the wire document is the constant, not the profile's"** — and this one
  could not be killed behaviourally, which is the honest result rather than a
  missing case. The frozen schema pins `client_capabilities` to exactly
  `{"fs": {}, "terminal": false}`, so a stored profile that reaches emission
  *cannot* differ from the constant; the two are indistinguishable today. They
  are not the same code, and W641's defect was one constant standing for two
  documents — so the property is checked where it lives, structurally: the
  emitted value is the profile's member, passed through the rule.
- **H15, "the capability answer is walked unowned"** — killed all along, by the
  witness in the inventory's `StatedRules`, which the first harness did not run.
  My harness was measuring less than I claimed for it; re-run with that class,
  it dies.

**An operational note, because it bit twice.** A mutation run left a mutant in
the tree — the same defect this campaign already recorded once. This time the
cause was mine and worse: I put `timeout` around the harness, the kill skipped
the `finally` that restores, and a *second* harness then ran against a source
another process was still rewriting. Two mutants (H4, then H5) had to be
restored by hand. The fix is not a bigger timeout: the harness now runs against
the fast suites so it finishes in seconds, and the source is compared against a
pristine copy after every round. Both comparisons are clean.

## Verification

- `tests.manager.test_handshake` — 29 methods, all pass.
- `tests.manager.test_boundary_inventory` — 67 methods, all pass.
- Full Python source suite and `just gate` — see the evidence for the counts.

## What is deliberately not here

- **The contracts-package inventory (cut B).** It is the Job's second
  deliverable and is a separate cut with its own review, which is what umbrella
  item 20 asked for. Cut A is what W1593 waits on.
- **The rest of the handshake**: agent method surfaces, agent-origin routing,
  the App Server's provider binding, sessions, turns and event normalization.
- **W1593's acceptance.** Its boundary now exists and this cut proves the wide
  record refuses under `policy.denied` in under 500 characters; W1593 exercises
  it from its own claim rather than having this Job write its acceptance.
- **§13 and retention.**

## The two P1s, corrected — 2026-08-24

Both were mine and both were right.

**A Boolean was accepted as wire version 1.** `negotiate_acp` compared with
`!=` alone, and Python's equality relation says `True == 1` — so an agent
answering the Boolean `true` negotiated as ACP version 1. The frozen reference
compares with JavaScript's type-strict `!==`, which never had that reading, so
this was a **port defect** rather than a permitted difference: Python's `==` is
wider than the contract. The type is now established before the value.

**`_offered` owned a broader value than the contract it claimed.** `own` admits
any exact built-in JSON value, so a *record* whose six keys were the capability
names passed as though it were the list — `name for name in {...}` walks a
dict's keys — and a real list carrying the six plus `1`, `true` or `null`
passed too, because the projection dropped what it could not use. It now
establishes **one exact built-in list of text**, and a member it cannot read is
a **refusal** rather than something dropped: dropping it means the manager and
the agent disagree about what was advertised and neither finds out. The refusal
carries the caller-local `refused.capability` pair, because a malformed
capability answer is the agent failing to present what 1.0 requires — not
`integrity.schema`, which would say this manager received a malformed document
from somebody whose contract it owns.

Measured directly, not just through the suite: Boolean `true` →
`refused/unsupported-version`; a six-key record, and the six plus `1`, `None`
or `True` → `refused/capability`; the honest six → accepted.

`tests.manager.test_handshake` is **31/31**, including the reviewer's five
added subcases.

## State

**Awaiting re-review of the corrected cut A.** The full source suite has six
failures and **none is W6592's**: five are the boundary-inventory declaration
table for `workspaces.py` and `oci.py` (W6631 and W6632, where I recorded them
as unfinished), and one is a reviewer-added mount case in W6632's suite that I
have not seen before and have not touched under this claim.

## Re-review corrections — 2026-08-25

**[P1] An old journal result was replayed after its effect was replaced.**
Correct, and the sequence is exactly as the review states: certify A, certify B
under the same profile id, certify A again — the third call replayed A's
journalled success, skipped the upsert, and **answered that A was certified
while the row still held B**. `certified_agent_session_profile` correctly
reported A absent, so the operation contradicted itself.

The mistake was using the journal's effectively-once contract for a
**replaceable state-setting** effect. The journal answers "did this operation
already happen"; an old row answering yes is not proof that its effect is still
current, and `(kind, name)` is the profile's identity — recertifying one id
under new bytes changes the one current profile, which the store's schema says
in as many words.

The effect is now performed every time, and that is safe because the upsert is
**idempotent on state**: running it twice with the same bytes leaves exactly
what running it once leaves. That is what effectively-once must mean for a
state-setting operation — the same answer *and* the same state, not a cached
answer and no state. The frozen host's own certification path is unjournalled
for this reason, which is where the review pointed and where the answer was.

**[P2] The module narrative named the superseded placement.** `handshake.py`
still said §2.2 was reached from the certification path while the
implementation, PROGRESS and PLAN all place it at emission. Corrected, and the
replacement says so explicitly — two contradictory placements in one contract
is worse than either.

`test_handshake` is 32 and `test_store` 48 — 80 passing.

**And I fixed the root the review attributed elsewhere.** The 334-failure
cascade in the shared inventory came from
`workspaces.py:materialize_directory_source` passing a non-literal boundary
label — **my own regression**, introduced when I applied W6631's
fragment-validation correction. It is W6631's file and I touched it under this
claim, which I would normally not do; the review makes the shared gate a
condition of this Work's signoff and it was a one-token fix restoring a literal.
The inventory is now **5 failures rather than 334**, and those five are the
genuine declaration-table entries for `workspaces.py` and `oci.py` that W6631
and W6632 both record as outstanding.
