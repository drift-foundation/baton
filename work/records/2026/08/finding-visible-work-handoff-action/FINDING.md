# Surface the current handoff action in Work details

## Observed — 2026-08-19

After W459 passed to `baton.ops`, its durable pass comment said exactly what
the operator needed to do after deployment. The Work's Messages view did not
show that recap because `pass` is intentionally a threadless Work event. The
operator read Messages, saw no final recap or next action, and reasonably
concluded that the instruction was absent.

## Confirmed boundary

Do not turn a pass into a discussion message. That would reintroduce thread
selection ambiguity and move message/New counts for a workflow transition.
The authoritative handoff remains one threadless event in the Work journal.

The TUI nevertheless needs to surface the latest actionable handoff where a
handler or recipient naturally looks. Work details should show a compact
current-action summary independent of whether the Messages or Events tab is
selected. It must identify the actor, destination, time, and pass comment, and
must not masquerade as a Message or affect Message/New counts.

## Acceptance boundary

- A Work passed with a comment exposes that comment prominently in Work
  details without requiring the operator to discover the Events tab.
- Messages remain discussion messages only; their counts do not change.
- Events remains the complete authoritative journal and carries the full pass
  payload.
- The summary follows the latest applicable handoff and cannot show an older
  instruction after a later pass, close, or correction.
- JSON clients can obtain the same current-action fact without scraping TUI
  prose.
- `docs/EFFECTIVE-BATON.md` explains that pass comments are threadless Events,
  how the current-action summary relates to that journal, and what the
  recipient does next. Documentation complements the visible UI; it is not a
  workaround for hiding the handoff.

## Scope correction — 2026-08-19

The proposed protocol projection and mandatory Work-detail summary above are
superseded. Slawomir clarified that a useful final recap and next-action note
is an operating convention: Baton can require non-empty prose but cannot judge
whether that prose is a sufficient recap.

The enforceable behavior already exists: `pass` is a threadless authoritative
Event with a required comment. The human/agent convention belongs in
`docs/EFFECTIVE-BATON.md`: when continuity through the discussion matters,
leave a concise final Message naming what finished, what remains, and the next
expected action, then perform the authoritative pass. Events remains where the
transfer itself is audited. No new JSON projection, message-count behavior, or
TUI action-summary feature is required by this finding.

### Human handoff clarification

For a handoff to a human reviewer or approver, the final discussion Message is
required by operating convention, not merely optional when convenient. It
must state the result or current status, the decision or action now expected
from the human, and the recommended next step. The human is not expected to
deduce that instruction by reading a series of Work Events; synthesizing the
journal into a clear handoff is the agent's job. The subsequent `pass` records
the authoritative workflow transfer.
