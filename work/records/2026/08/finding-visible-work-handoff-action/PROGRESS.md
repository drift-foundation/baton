# Progress

Implementer-owned.

## Revalidation against the current tree — 2026-08-20

The scope correction is promoted as this Work's revision 1, so the
contract I implemented is the corrected one and not the original
finding: an operating-guide change, with no projection, no TUI feature
and no message-count behaviour.

I checked that the correction still matches the tree before writing to
it. `pass` is threadless and requires a non-empty comment; the guide
already said so, one paragraph above where this belongs, and already
promised that a pass "creates no message and moves no conversational
count". What was missing was the CONSEQUENCE of that design — an
operator reading Messages will not see the comment — and the habit that
answers it.

## What changed

`docs/EFFECTIVE-BATON.md` gains **"Say it in the discussion before you
hand it over"**, inside the straight-through path, immediately after
`set-next` and before the phase section. Placement is deliberate: an
operator meets it while reading about `pass`, not in an appendix.

It says three things.

**Where the comment lives, and what follows from that.** Durable,
authoritative, in the Events journal — the right home, because a
workflow transition must not inflate a discussion count or make
somebody choose a thread — and therefore invisible to a reader of
Messages. That last clause is the whole finding.

**The habit**, with both commands in order: `say` the recap, then
`pass`. Two records, each doing its own job.

**The human rule**, as the promoted contract words it: handing Work to
a human reviewer or approver, the message is NOT optional, and it
states the result or current status, the decision or action now
expected from the human, and the recommended next step. A human must
not have to reconstruct that from a series of Events; synthesising the
journal into a clear handoff is the agent's job.

It closes by naming itself: Baton requires a non-empty comment and
cannot judge whether prose is a sufficient recap, so this is a
convention kept because it works, not a rule the authority enforces. A
guide that implied enforcement would promise something the product does
not do.

## Verification

- `tests/work/test_w1100_handoff_recap.py` — new, **10 passed**. It
  reads the SECTION rather than the whole guide, so a phrase elsewhere
  cannot satisfy a check about this one: the pass comment named as not
  a message with the consequence spelled out; the example ordering
  `say` before `pass`; all three ruled elements of a human handoff;
  the "must not have to reconstruct" rule; the convention-not-
  enforcement framing; the pass still being the authoritative
  transfer.

  Two of them pin the SCOPE CORRECTION rather than the prose: the
  section must not describe a current-action summary or a handoff
  projection, because that is the half this Work superseded and a
  guide describing it would document a feature nobody built.

  One is mechanical, in W104's spirit: every verb and operand the new
  example uses must exist in `cli.GRAMMAR`.
- `test_w104_effective_baton.py` — **12 passed**, unchanged. Its own
  checks are deliberately mechanical and assert no prose completeness,
  which is why this Work's prose has its own file rather than being
  bolted onto that one.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2599 passed** (parallel), **40 passed** (serial), **55 passed / 0
  failed** in the bridge suite.

## Practised on the way out

The handoff of this Work follows its own ruling: the recap goes on
thread T1100 as a Message, and the `pass` that follows carries the
durable comment. If the convention were not worth keeping here, it
would not be worth writing down.

## What I did not do

No code. The original finding's Work-detail summary and JSON
current-action projection are superseded by revision 1, and building
either would have been implementing a contract the record explicitly
retired.

I also did not add the convention to `docs/AGENTS-MAILBOX-PROTO.md`.
That document is the protocol contract — what the authority accepts and
refuses — and this is deliberately not enforceable. Putting it there
would blur the line the guide's own subordination rule keeps.
