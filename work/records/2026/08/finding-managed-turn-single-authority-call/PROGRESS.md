# Progress — Invoke managed Baton mutations one command at a time

## Items 2 and 3 implemented — 2026-08-23

Implementer: baton.claude. Evidence:
`evidence/implementation-2026-08-23.txt`. Baseline before any edit matched the
reviewer's: 24 Python, 27 Node.

### The rule, and a regression that keeps it where it belongs

The bullet is the first rule of "Non-interactive managed turns", immediately
after "The active-work claim". A rule about the mandatory claim, filed
somewhere a reader of the claim rules never reaches, is a rule that will be
missed the same way this one was.

So the regression asserts POSITION as well as text. Text a regression only
greps for can drift to the bottom of a file and still pass.

### The shape, not the outcome

`readinessClaimOutcome` decides the ordered two-item shape. The reason it
cannot be an outcome check: **"the Work is claimed" is equally true of one
batched command that happened to work**, of a claim issued before the read,
and of three attempts of which one landed. None of those is the boundary.

It is deliberately separate from `requestedItem`, which requires exactly ONE
command item and would refuse this shape as "the turn also ran something
else". One command per turn was right for the policy matrix; this Work is
about the turn that legitimately runs two.

Eight deterministic regressions, including the defect itself: `detail` and
`claim` in one item is refused as "exactly two".

### The live proof is RED, and I did not weaken it

Three live runs against the running app-server failed the new assertion, for
two reasons that are operational findings rather than something to assert
around — recorded as plan items 5 and 6.

**`thread/read includeTurns` returned no command item for a turn that
demonstrably ran a command.** The agent message was a real Python traceback
from the deployed executable, so a command certainly ran. A separate minimal
probe reproduces it with one `/bin/echo`. `CommandExecutionThreadItem` is in
the installed schema, so this is the server not recording it — and **it is the
premise W2845's command oracle rests on.**

**The managed invocation ended in an unhandled traceback**, not the typed JSON
error every other refusal uses, consistent with the read-only database this
Work is about. The same commands succeed cleanly outside the sandbox, verified
with no model involved.

I did not relax the assertion to accept zero command items, fall back to the
committed Handler alone, or touch `exec_policy.mjs`. Any of those would have
produced a green live proof that established nothing — the exact failure mode
the W2845 oracle exists to remove.

**What the smoke gained from failing:** it now dumps every item of the turn
when the shape does not hold. The defect this Work exists for was invisible
because the visible symptom was an idle reviewer beside pending Work, and an
assertion that fails without saying what the turn did repeats that.

### Verification

- `pytest -n auto -m "not serial" tests/work` — **2977 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**.
- codex-event-bridge 324/324; acp-baton-bridge 55/55; v12 492/492;
  whitespace clean.
- Focused baselines moved 24 → 25 Python and 27 → 35 Node, by exactly the
  cases added here.
- The live smoke is excluded from every suite above, as it always has been.

### State

**Awaiting independent review.** Item 4 remains an operator gate, and items 5
and 6 are what currently stand between this Work and the live proof.

## Corrected — 2026-08-23

`review-2026-08-23T04-30-59Z.md`, two P1. The reviewer's pure counterexample
reproduced against the shipped oracle before any edit: a completed read at
exit 7 beside a completed claim at exit 0 returned `{ ok: true }`. Both
correct. Evidence: `evidence/correction-2026-08-23.txt`.

### The contradiction I left in my own proof

The thread-level developer instruction still said "exactly the ONE canonical
Baton operation", while the turn now asks for two. Developer instructions
outrank the turn input, so the model was handed a contract it could not
satisfy — and I changed the turn without re-reading the thread it runs in.

A proof whose two halves disagree cannot diagnose anything. Mine could not
have told a model that ignored the standalone rule from one that obeyed the
instruction outranking it.

### Completed is that it ran, not that it worked

`readinessClaimOutcome` never read `exitCode`. The Handler assertion
afterwards catches a claim that did not commit; **nothing caught a failed
read** — and the read is the half that *succeeded* in the defect this Work
exists for. The one item my proof could not check was the one the original
failure left looking healthy.

### The live re-test, and where the absence went

Re-run with the contradiction removed: still no agent command item. So it is
routed out as the review instructed — **W7989**, cross-referencing W2845, with
its own dossier. W7830 is blocked on it. The W2845 edge could not be recorded
from here (`baton.claude` is not its handler while it sits with `baton.bug`).

**One correction to my own earlier report:** the *smoke* run was confounded by
the contradiction and could not have shown the server finding on its own. The
two *probes* were not confounded — single command, no contradictory
instruction, and the nonce probe caught a turn having run one with no item
recorded. The finding stands on the probes.

### Verification

- codex-event-bridge **329/329**; focused W101+W220 Python **25 passed**;
  whitespace clean.
- Two mutations witnessed; the third recorded as not mechanically checkable.
- The live smoke is red, for the reason now recorded as W7989.

### State

**Awaiting re-review**, and blocked on W7989 for its live gate.
