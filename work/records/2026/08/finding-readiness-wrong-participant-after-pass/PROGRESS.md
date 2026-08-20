# Progress

Implementer-owned.

## Reproduced, and located — plan step 1

The defect is real and I found where it is NOT before deciding where it
is.

**The projection is clean.** `participant_actions` moves Work off the
old participant and onto the new endpoint in the same transaction as
the `pass`, under a NEW episode key. I proved it against a fixture with
two routes and DIFFERENT handlers — which matters, because the ordinary
test fixture routes every kind through one route with one handler, and
on that shape a pass looks like it changes nothing. My first attempt
used it and "reproduced" the bug; it was the fixture, not the product.
`tests/work/test_w1224_stale_readiness.py` is that half, including the
held-Work case and a pass/claim/pass race asserted after EVERY step.

**The window is the Codex dispatcher's queue.** An event forwarded by
the readiness producer sits in `state.queue` until the target's session
is idle. If a turn is running it waits — and by the time it drains, the
Work may have been passed to another endpoint. That is exactly the
reported shape: a wake produced when the Work genuinely was actionable,
delivered after it stopped being.

The ACP bridge already closes this: `episodeStillLive` re-reads
`wait timeout=0` immediately before the turn and drops an action whose
key is gone ("W49: revalidate the exact episode IMMEDIATELY before the
turn"). The Codex path had no equivalent. One family of runners was
protected and the other was not, which is why this looked like a
Codex-specific defect while being a missing check.

## What changed

**The event carries its episode structurally.** `actionEvent` now emits
`action: {participant, key}`, and `normalizeEvent` validates and keeps
it. Structurally rather than by parsing the event id, because W148
rules that consumers key delivery on the whole action key and never
take it apart — a dispatcher re-deriving a participant from a string
would be doing precisely that.

**The dispatcher revalidates immediately before the turn.** In
`#drain`, a queued readiness event is checked with one cheap read of
the SAME participant's own projection, requiring that exact key to
still be there. Gone means dropped: dequeued, logged, an
`actionDropped` event emitted, and the queue keeps draining. No turn is
spent and no Work is touched.

**A check that cannot run never discards a wake.** No action block, no
`roleInstructions` to reach Baton through, a failed execution, or a
reply with no actionable set — all retain the event and let the
ordinary path continue. Only a SUCCESSFUL read that does not list the
key drops it. The opposite default would trade a misleading wake for a
lost one, which is worse: an operator can see a wake that should not
have come, and cannot see one that never did.

**It narrows the window rather than closing it.** A mutation can still
land between this read and the model's claim, so the atomic claim
remains the final authority and still fails closed — which is what the
finding asks for. What is removed is the misleading wake, not the
refusal behind it.

## Verification

- `tests/work/test_w1224_stale_readiness.py` — new, **8 passed**: a
  pass moving the wake in one transaction; the new participant getting
  a NEW episode key rather than the old one handed on; held Work never
  offered as unclaimed to anybody else; the holder still seeing its own
  Work as claimed, so the claimant-continuation half of `wait` survives
  the fix; a pass back waking the implementer exactly once; a
  pass/claim/pass race checked after every step with neither
  participant ever holding a wake at the same time; readiness writing
  nothing; and the CLI refusal still naming the endpoint that may act.
- `tools/codex-event-bridge/test/stale_episode.test.mjs` — new,
  **11 passed**, driving the real dispatcher: a dead episode dropped
  without a turn; the revalidation asking about the EVENT's
  participant rather than the target's, with the exact argv pinned; a
  live episode delivered once; a NEW episode for the same Work
  delivered; an ordinary build event never revalidated; a failed read,
  an unreadable reply, and a deployment with no `roleInstructions` all
  retaining the event; the action block surviving normalization; and a
  malformed one refusing the event outright.

  Removing the check makes three of those fail, which I verified rather
  than assumed.
- The Codex bridge suite — **135 passed**.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2558 passed** (parallel), **40 passed** (serial), both bridge
  suites green.

## One thing I did not do

The ACP and Codex paths now both revalidate, but through two functions
in two packages — `episodeStillLive` in the ACP bridge and
`#episodeIsOver` here. Sharing one would mean the Codex package
importing from the ACP package, which inverts the dependency direction
this repository already has (ACP imports the shared envelope validator
FROM codex-event-bridge). Moving the helper into the Codex package and
having ACP import it is the tidy answer, and it is a refactor of two
shipped components that this finding does not ask for. Flagged rather
than done.


## Response to review round 1

**P1 accepted.** My revalidation proved the episode was live for the
participant the EVENT names, and said nothing about whether that
participant is the identity the target runs as. So a structurally
valid event addressed to the tuner target while naming `baton.codex`
passed the check and woke the tuner session for somebody else's Work —
the same class of defect this Work exists to remove, reached from a
direction I did not consider.

I had the right question and asked it of the wrong pair. "Is this
episode still live" is not the same question as "is this episode for
this runner", and only the first was being answered.

**The two identities must agree, structurally, before anything else is
asked.** `#episodeIsOver` now compares `event.action.participant` with
`state.identity.participant` FIRST and drops on a mismatch, logging
both names. Checked before the canonical read deliberately: a mismatch
is not a stale episode to re-examine, it is an event that was never for
this target, and reading Baton about it would be answering a question
nobody should be asking.

The boundaries the review asked me to preserve are preserved. The key
is still checked against that same participant's canonical projection.
A target with no configured identity still cannot perform the
comparison, so it falls through to the existing fail-open path rather
than dropping. The atomic claim remains the final authority.

**One of my own tests moved.** `the revalidation asks for the EVENT's
participant, not the target's` proved its point by sending a mismatched
event and watching the read follow it — which is precisely the
behaviour now refused. The property it defended (the read names the
episode's own participant, with the deployment's own binary and
config) is still pinned, on a legitimate event, and the mismatch case
is the reviewer's own.

The reviewer's regression passes unedited, and I checked the other
direction: removing the identity comparison fails it alone.

- `tools/codex-event-bridge/test/stale_episode.test.mjs` — **13
  passed** (12 mine, 1 the reviewer's).
- The Codex bridge suite — **137 passed**.
- The complete v11 gate exits 0 after the round: **2589 passed**
  (parallel), **40 passed** (serial), both bridge suites green.
