# Progress: separate ACP wire capabilities from the durable profile summary

Implementer-owned. One writer: `baton.claude`.

## Implementation — 2026-08-23

### The ruling went further than my workaround, and that is the point

I raised this during the handshake slice, and on that review's instruction I
split the concept into two NAMED representations —
`ACP_WIRE_CLIENT_CAPABILITIES` for the transport and
`NORMALIZED_CLIENT_CAPABILITIES` for the durable profile. That was right while
the artefacts disagreed and the owner had not ruled: naming both is honest,
and it stopped snake_case field names going onto the wire.

The ruling did not ratify the split. It says agent-session 1.0 keeps ONE
representation, that it is ACP's, and that the snake_case explicit-false shape
is "the contract defect to remove, not a second representation to name". So
this implementation DELETES the second constant.

That is worth noticing as a pattern: a workaround that is correct as a
workaround can quietly become the design if nobody rules. The finding existed
precisely so it would not.

### Revalidated

The pinned SDK's filesystem capability members are OPTIONAL, so an empty `fs`
is a complete expression of "no filesystem capability". An explicit `false`
was never needed to say it — which is why omission semantics are the ruling's
load-bearing phrase.

### The re-seal

Changing the captured trace's profile changed its bytes, so its
`document_digest` moved. I re-sealed it through the model's own
canonicalization rather than by hand, and updated every v12 fixture carrying
the old value — the design-model-profiles-certify-unchanged case is what
proves those stayed in step.

### Two assertions that encoded the defect

One in the model asserted every `fs` member was present and `False`. One in
v12 asserted the profile's document was REFUSED as an advertisement, because
the two representations differed; that case is INVERTED now and renamed, and
asserts the profile persists the same document the relay sends and gets an
owned copy back. Both are marked superseded where they stood.

### What I deliberately did not change

The exact minimal-capability POLICY. Withholding is still total, `session` is
still stable and still not advertised, the eight client methods are still
denied. The ruling corrected which document expresses the policy, not the
policy.

### The gate, honestly

`cd v12 && npm test` is **639 passed, 6 failed** of 645, and none of the six
is W641's: two W543, two W4, and two W771 second-review cases that landed
while I was implementing this. W641's own suites are green — handshake 21/21,
profile 14/14, sessions 18/18 — and the ACP model is clean apart from W543's
two open cases.

### Verification

- design models: **64, 64 (1 fail 1 error — W543's round), 74, 24**.
- `cd v12 && npm test` — 639/645 as above; zero test-owned roots under a
  TMPDIR bracket.
- Three mutations, all witnessed. The first reinstates exactly the state this
  Work exists to remove and fails four cases.
- whitespace clean.

### State

**Awaiting independent review.** Plan item 5 — re-reviewing W4 and every later
adapter consumer against the corrected single contract — remains open.

## First correction — 2026-08-23

`review-2026-08-23T19-36-46Z.md`, one P1 and one P2. Reproduced before any
edit: 21 of 23, exactly the two additive regressions. Both findings are
correct. Evidence: `evidence/correction-round1-2026-08-23.txt`.

### I asked whether the object looked empty, not whether it was the document

`Object.keys(new Date(0))` is empty and a Date is not the empty JSON document
— it serializes as a **string**. Counting enumerable members answers "does
this look like `{}`"; the question this boundary exists to ask is "is this the
document §2.2 sends". Those are different questions and only one is about the
wire.

An inert JSON record is proved at both levels now, and it is four things: an
object that is not an array; carrying `Object.prototype` or none, so nothing
inherited decides its wire form (which refuses Date, Map, RegExp and every
class instance **generically**, rather than by a list of the exotic types this
contract happens to know today); with exactly the expected own keys **counting
the ones `Object.keys` hides**, because a non-enumerable `toJSON` is invisible
there and decides the entire serialization; and every member a **data**
member, because a getter may answer one thing to the check and another to the
wire.

`Object.create(null)` and either insertion order remain valid, as required.

### The refusal serialized what it refused at three sites, not one

The review found `JSON.stringify(advertised.terminal)`. The envelope refusal
and the `fs` refusal carried the same line and the same defect — a BigInt
escaped as a raw `TypeError` from either. **A rule applied at one of three
sites is not applied.** All three name the value by its shape now, through one
helper that runs nothing. Member *names* are still reported: a property name is
an inert string and "which members did you send" is the whole diagnostic. What
is never reported is a value.

And the envelope is proved **before** its members are read, which is what makes
those two reads inert.

### Two zeros, investigated, with different answers

Nine mutations; seven witnessed. One is **provably** equivalent rather than
merely unwitnessed: `Array.isArray` throws on exactly one kind of value, a
revoked Proxy, and every reflection on a revoked Proxy throws — so the
prototype read fails first and the array line is never reached with a value
that could make it throw. Notably this is the *opposite* of W2929's fifth
review, where the same operation ran *before* the prototype read and was
load-bearing. Same operation, different position, different answer.

The other zero was a **missing case**: reaching the descriptor read needs a
Proxy that answers the right prototype, the right member names, and then throws
from its `getOwnPropertyDescriptor` trap. I built that value and added it.

**A zero is a question, not a result**, and I could not have told these two
apart without asking.

### A duplication reported rather than resolved

`agent_reconnect.mjs` now carries its own `classify`/`isPlainRecord`/`describe`
with the same rules, from W2929's fourth and fifth corrections. I did not unify
them: that module is inside W4's open review round — a sixth review of it
landed while I was working here — and moving code out of a module under review
puts the change in the wrong Work. Recorded as plan item 7, for W4 composition.

### Verification

- handshake **26/26**, profile 14/14, session 18/18.
- `cd v12 && npm test` — **661 tests, 659 pass, 2 fail**; zero test-owned roots
  under a TMPDIR bracket. Both remaining failures are W4's *new* sixth-review
  cases in the reconnect suite, untouched here.
- design models 64/66/24/74; v11 pytest 2980 and serial 52; codex-event-bridge
  336; acp-baton-bridge 55; schemas byte-identical; whitespace clean.

### State

**Awaiting re-review.** Plan items 7 and 8 remain.

## Second correction — 2026-08-23

`review-2026-08-23T20-20-01Z.md`, one P1 and a required composition.
Reproduced before any edit: 26 of 28, exactly the two additive regressions.
Evidence: `evidence/correction-round2-2026-08-23.txt`.

### The P1 arrived twice, in two copies of one rule

A Proxy whose traps **answer** passes a record proof built to catch traps that
**throw**. Both capability levels accepted one, and caller code ran while
policy was being decided.

This is the same defect W2929's sixth reconnect review found in the *other*
copy of these rules, one round earlier. I raised the duplication as plan item 7
yesterday and said it would cost something. It cost this.

### One record proof now, and the callers keep their own taxonomies

`v12/src/worker_manager/records.mjs` — `classify`, `describe`, `isPlainRecord`,
`recordFault`. Both boundaries call it; neither keeps a copy. A Proxy is
rejected first by a non-observing discriminator, because a successful trap
walks past a try/catch.

The module returns **facts and prose, never a `ContractError`**:
`integrity.schema` at reconnect and `policy.denied` at the capability envelope
are the callers' policies, and a shared primitive that threw one of them would
be deciding something that is not its business.

Its header carries the six rules six review rounds produced — don't serialize
the value, don't read it, don't interview what was thrown, "runs no user code"
is not "cannot fail", translating a trap that throws does nothing about a trap
that answers, and looking empty is not being the empty document. Every one was
learned by getting it wrong, and none of them is obvious from the code.

### Touching reconnect while W4 is in review

I declined to unify yesterday because `agent_reconnect.mjs` sits inside W4's
item 4af, which is with `baton.feat` now. This review overrides that
explicitly. **No assertion in either suite changed**: I made the shared
vocabulary reconnect's *existing* vocabulary precisely so W4's in-review cases
keep passing unedited. The only call-site changes there are an import and one
argument order.

### Two zeros again, different answers again

Eight mutations. S1, S2 and S6 fail cases from **all three** suites, which is
the composition working: one guard, three sets of witnesses.

One zero was a missing case, and a real one — a bare array is refused by the
prototype rule and a dressed one by the Proxy test, so nothing reached the
array line; but `Object.setPrototypeOf([], Object.prototype)` is an **ordinary
array**, no Proxy involved, wearing the document prototype and still
serializing as `[]`. Added.

One is measured **unreachable, and became unreachable in this correction**: the
descriptor wrapper's only witness was a descriptor-trapping Proxy — my own
witness last round — which the Proxy test now rejects long before. Kept for
host exotica, not counted as a guard.

### A suite for the primitive itself

Six cases. What neither caller can state is that **these functions answer** —
answering never throws and never runs the value. That is the property that
makes them safe to share: a shared helper that can throw turns one caller's
refusal into another caller's crash. Ten hostile values across five entry
points, all thirteen Proxy traps and seven throwing accessors instrumented.

### Verification

- records **6/6**, handshake 28/28, reconnect 32/32, profile 14/14, session
  18/18.
- `cd v12 && npm test` — **670 tests, 670 pass, 0 fail**. The full v12 gate is
  green: every open review round across W4, W543, W641 and W771 now passes and
  there is nothing left to attribute to another Work.
- design models 64/66/24/74; v11 pytest 2980 and serial 52; codex-event-bridge
  336; acp-baton-bridge 55; schemas byte-identical; whitespace clean; zero
  test-owned roots under a TMPDIR bracket.

### State

**Awaiting re-review.** Item 7 is discharged; item 10 remains. Carried from W4:
a Proxy session *reference* still runs four `get` traps in
`normalizeAgentSessionRef` — the same class of defect on a different operand,
raised there for a ruling. If it is ruled in, this module is where it belongs.

## Third correction — 2026-08-23

`review-2026-08-23T20-37-50Z.md`, one P1. Reproduced before any edit: records
6/7 and handshake 28/29, exactly the two additive regressions. Evidence:
`evidence/correction-round3-2026-08-23.txt`.

### The rule has two directions and I implemented one

Round one established "looking empty is not **being** the empty document", and
I implemented it by counting hidden own keys — so an EXTRA non-enumerable
member could not smuggle a `toJSON` past the proof.

Then I proved the EXPECTED members by property access alone. An envelope whose
`fs` and `terminal` were both non-enumerable passed: both values readable,
`JSON.stringify` of it `{}`. The validator answered "can I read these off this
object" when the contract asks "is this that document" — the exact distinction
the Date correction established two rounds earlier, at the other end of the
same function.

**I had the rule and applied it to the members I did not expect.** The ones I
did expect got the older, weaker question. `recordFault` now requires every
expected member's descriptor to be enumerable as well as a data descriptor,
still as an inert descriptor check.

### The case asserts the property, not the branch

Asserting the new branch would repeat the mistake in test form — checking the
direction I just noticed. So the case asserts, over five accepted spellings,
that **acceptance implies the JSON document**, checked by round-tripping
through `JSON.stringify` and comparing the actual wire keys.

And it says explicitly that the converse is **not** claimed: a hidden extra
member does not change the wire form either, and the proof refuses it anyway,
because a document carrying invisible state is not the document. The rule is
stricter than the wire on purpose, and four refusal cases state that edge.

### Verification

- records **9/9**, handshake 29/29, reconnect 32/32 with no assertion edited,
  profile 14/14, session 18/18.
- `cd v12 && npm test` — **677 tests, 677 pass, 0 fail**. W4's composition
  revalidation landed while this was in review and is included in that count.
- Four mutations, all witnessed, including re-measuring the two neighbouring
  rules to confirm this did not make either redundant.
- design models 64/66/24/74; v11 pytest 2980 and serial 52; codex-event-bridge
  336; acp-baton-bridge 55; schemas byte-identical; whitespace clean; zero
  test-owned roots.

### State

**Awaiting re-review.** Item 12 remains. Carried from W4: the
session-reference container question is an open ruling, and if references are
ruled inert this enumerability rule is exactly what would stop one from
carrying hidden state.
