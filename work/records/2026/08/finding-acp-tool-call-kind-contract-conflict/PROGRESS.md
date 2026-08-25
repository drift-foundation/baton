# Progress: reconcile ACP tool-call kind across prose and schema

Implementer-owned. One writer: `baton.claude`.

## Implementation — 2026-08-23

I raised this conflict during the event slice and declined to resolve it
there, which was right — two frozen artefacts disagreed and picking one would
have been an implementer choosing a contract. The ruling picked, so this is
implementation rather than judgement.

### Revalidated against the SDK, because that is the whole point

The ruling required revalidating the pinned provider shape rather than
inferring the answer from the W4 code or its tests. Done, and it confirms
every clause: `@agentclientprotocol/sdk` 1.3.0 declares `kind?: ToolKind` on
`ToolCall` and `kind?: ToolKind | null` on `ToolCallUpdate` — permitted, never
required — and its `ToolKind` is exactly the ten the ruling names. The SDK's
own comment on the member, "Helps clients choose appropriate icons and UI
treatment", is the presentation-only boundary.

### One change, seven artefacts, and the superseded text quoted

§6.2's row, a new §6.2.1, the frozen schema's `toolCallView` and a new
`toolKind` definition, the owning FINDING, the executable model, the
byte-identical product copy, and the v12 normalizer and tests — all in one
act, which is what "finish in one state" means. The product-schema-matches-
the-frozen-asset case is the one that proves it, and it passes.

§6.2.1 QUOTES what both artefacts used to say. A reader who finds the
correction needs to know which way it was resolved and why, not just what the
answer is now.

I also routed the model's trace-driven case through `normalize_tool_call`
instead of building a view inline. The model had two tool-call boundaries and
only one of them was the contract.

### The assertion I wrote pending this ruling

v12's tool-call case ended by asserting that a supplied `kind` must be
DISCARDED. I wrote it during the event slice precisely because the artefacts
disagreed. W543 supersedes it, so it is replaced — and the comment above it
says what it used to require and on whose authority it changed, rather than
just being gone.

### "Absence does not become other" is the case worth having

The inference that would look most reasonable is filling a missing kind with
`other`, since `other` is in the vocabulary and means "unclassified". So the
absent case drives a RICH update — a title, a tool name, a command and a
status all present — and asserts the member is still absent. A missing kind is
missing evidence.

And the durable case asserts the field decided nothing: the event's own kind
still comes from the §6.2 mapping and no column carries the tool kind. "No
permission, policy, tool authority, turn outcome or disposition" is
implemented by nothing reading it.

### The gate is not all green, and none of it is this Work's

`cd v12 && npm test` is **628 passed, 7 failed** of 635. All seven are
additive reviewer regressions that landed while I was implementing this, in
two suites W543 does not touch and which contain no reference to a tool-call
kind: two "W2929 third review" cases on the transport-loss options envelope
(W4), and five "W771 review" cases on the posture-slot lifecycle (W771).

The W543-owned suites are **112 passed, 0 failed**. I did not fix the others
under this claim; both Works are queued for their own rounds and correcting
them here would put the change in the wrong record.

### Verification

- design models, all four: **64, 61, 74, 24** — the ACP boundary model moved
  56 → 61 with the five new cases.
- `cd v12 && npm test` — 628/635 as above; zero test-owned roots retained
  under a TMPDIR bracket.
- W543-owned suites — **112 pass, 0 fail**, including the byte-identity case.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

### State

**Awaiting independent review.** Plan item 5 — re-reviewing every consumer
against the corrected single contract — remains open and is not discharged by
this implementation.

## First correction — 2026-08-23

`review-2026-08-23T19-05-30Z.md`, one P1 and one P2. Reproduced before any
edit: exactly the four additive regressions failed, in both consumers. Both
findings are correct. Evidence: `evidence/correction-round1-2026-08-23.txt`.

### I quoted the distinction and then implemented one path

The v12 comment and the model docstring both state the pinned declaration
verbatim — `kind?: ToolKind` on `ToolCall`, `kind?: ToolKind | null` on
`ToolCallUpdate` — and both then treated null as absence on either source,
which erases the only difference that declaration states. The v12 fixture even
supplied `kind: null` on `tool_call` under a comment saying null was the
absence form *for an update*.

Both consumers now carry their source. The model had none at all and reads
`sessionUpdate`; a source it cannot see is not proof that a null was
permitted, so it refuses on the strict side. The whole table — omitted,
explicit undefined, explicit null, pinned value, anything else, against both
sources — is now in §6.2.1 as well, because prose that stops one step short of
the consequence is how this Work started.

**Documenting a distinction is not implementing it.** That is the second time
in two Works I have written a rule into a comment and left a call site outside
it.

### The refusal ran the value it was refusing

Two mechanisms, one shape: `JSON.stringify` in the JavaScript diagnostic threw
on a BigInt, and `x not in frozenset` HASHED the value in Python. Both now test
shape before membership and neither message names the value — `typeof` and
`type(x).__name__` cannot run provider code and cannot fail. Python uses
`type(x) is str` rather than `isinstance`, because a `str` subclass can
override `__hash__`.

This is the rule I was taught over four rounds on the reconnect primitive. It
applies to the diagnostic, not only to the check.

### A suite whose result depended on the runner

While reproducing I found that this Work's own `ToolCallKind` class sat BELOW
`if __name__ == "__main__": unittest.main()`. Run as a script the module never
reached the class: 57 tests, with every W543 model case inert. The reviewer's
runner found them; the file's own entry point did not. Class moved; both
runners now report 66 and agree.

### Two measurements I had to correct rather than believe

One JavaScript mutation — membership without the shape check — measured ZERO,
and it is genuinely equivalent: `Array.prototype.includes` uses SameValueZero,
so it coerces nothing and already refuses a BigInt or a String object. The
leak was entirely in the diagnostic. Reported as equivalent, not counted.

One Python mutation measured zero because my harness scraped `... FAIL` from
verbose output and `subTest` failures are not printed that way. Read from the
FAILED/ERROR summary instead, that mutation is witnessed fourteen times over.
A zero from an instrument I wrote is a claim about the instrument first.

### Verification

- Design models 64 / **66** / 24 / 74, all OK, and the ACP boundary model now
  reports 66 under both runners.
- `cd v12 && npm test` — **654 tests, 650 pass, 4 fail**; both W543 review
  regressions pass. The four are two W641-review and two W4 fifth-review
  cases, in suites this Work does not touch.
- v11 pytest 2980 passed, serial 52 passed; acp-baton-bridge 55/55.
- Frozen and product schemas byte-identical; whitespace clean; zero test-owned
  roots under a TMPDIR bracket.

### State

**Awaiting re-review.** Plan item 7 (was 5) remains: the sweep found no
runtime reader beyond these two consumers, repeated after the change with the
same result, so what is left is confirmation at W4 composition.
