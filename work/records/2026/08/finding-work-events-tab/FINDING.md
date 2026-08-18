# Finding: Work needs a separate Events play-by-play

## Confirmed decision — 2026-08-17

**Approved by Slawomir during the v11-only trial.** Opening a Work defaults to
Messages, but Work detail also exposes a separate, visible `Events` tab.
`Events` is the concise authority-aligned label; documentation may describe it
as the Work's append-only journal or operational play-by-play.

The two views have distinct contracts:

- Messages contains human and agent discussion organized by Threads. Its
  `Msg`, `My`, and `New` semantics remain conversational and are not inflated
  by workflow transitions.
- Events explains what happened to the Work as an operational object and why.
  It includes creation, classification, priority and contract changes,
  bindings, dependency additions/removals, claims, heartbeats, releases,
  phase/Current/Next changes, passes, verification lifecycle, and terminal
  disposition.

Dependency changes appear through the same one authoritative event in BOTH
affected Works. For `unblock work=W2 on=W76 rationale=...`, W2 says it no
longer waits on W76 and W76 says it no longer blocks W2. Selecting either
projection shows the same actor, timestamp, typed event identity, and
rationale; storage is not duplicated.

Claim intervals supply the work-time play-by-play. An open claim has a start
and ongoing Held duration; release, pass, a newly invalidating gate, or close
ends the interval. Heartbeats remain recorded liveness evidence and never
rewrite the claim start or fabricate additional work time.

## Presentation boundary

- Work detail visibly offers `Messages` and `Events`; Messages is the default.
- From anywhere in Work detail, `]` switches to the next tab and `[` to the
  previous tab. The footer always discloses `[/] tabs`; this navigation is not
  discoverable only by prior knowledge.
- Each tab preserves its own focused pane, selection, and scroll position when
  the operator switches away and back. `Ctrl-W` continues to navigate panes
  inside the active tab; `Esc` returns from Work detail to the Work list.
- The Events list is human-readable, ordered by authoritative sequence, and
  paged. Selecting an entry shows its complete typed details and rationale.
- Routine events may be compact, but the authoritative sequence is complete;
  filtering or folding must be explicit rather than silently omitting history.
- Message bodies stay in Messages. An operational event caused by a message
  may identify that message/obligation without duplicating its body.
- JSON/CLI expose the same event identities, relationships, durations, and
  typed details without TUI glyphs carrying exclusive meaning.

This is independent follow-up usability Work. Its absence does not revoke the
successful v11 communication capability trial or block W2 closure.

## Revalidated implementation boundary — 2026-08-17

**Confirmed:** no schema change is required. The immutable `events` rows
already carry global sequence, typed kind, actor, timestamp, structured
payload, and act references. The live authority can therefore gain this view
without reinitialization. The existing global `events` read is not sufficient:
it is not Work-relative, does not name each Work's relationship to a shared
event, and offers no claim-interval projection.

**Proposed implementation contract, consistent with the approved UX:** the new
canonical JSON read is `work-events work=WORK` with bounded paging.
It returns each underlying event once for that Work, preserving the event's
real sequence and adding:

- `roles`: why this event belongs to the selected Work (for example subject,
  parent, child, consumer, blocker, provider, predecessor, successor, or
  duplicate target);
- `related`: the other explicitly affected Works and their roles;
- references already attached to the authoritative act;
- for claim boundaries, one structured interval naming claimant, start event
  and time, optional end event/kind/time, and elapsed seconds.

Association is an explicit event-kind contract, never a heuristic search for a
Work-shaped string inside arbitrary JSON. Direct `payload.work` events attach
to that Work. Dependency addition/removal attaches to both `work` (consumer)
and `blocker`. Creation attaches to the created Work and, when present, its
parent and closed predecessor; accepted provider Work, duplicate target, and
thread-label lifecycle acts similarly name their typed relationships. Pure
discussion posts and personal seen-cursor movement stay exclusively in
Messages and do not flood Events. Workflow-bearing message acts—requests,
responses/disposals, trial assignments/reports/assessments/withdrawals, and
contract promotion—remain Events without duplicating a message body.

A claim event is the interval identity. Release, pass/return, entry into
waiting/parked, a newly invalidating gate/child, or terminal close records its
end. The same interval facts are available from its ending event. Heartbeats
appear as compact events inside the interval and never become a new start or
change elapsed work time.

The JSON page stays in canonical ascending sequence order. The TUI opens the
newest bounded page and presents it newest-first, matching Messages; `n`
reaches older Events and `p` returns to newest. Both directions use a proof row
(`limit + 1`), so an exactly full final page never advertises an empty
continuation.

The detail header visibly renders `Messages  Events` with the active tab
distinguished. `]` selects the next tab and `[` the previous from anywhere in
Work detail; the footer always advertises `[/] tabs`. Events has its own index
and reader panes (`E<seq>` is the visible stable event identifier). Its reader
uses human labels for the common typed fields and still exposes the complete
payload, roles, related Works, references, rationale, and interval facts.
Switching tabs preserves each tab's focused pane, selected id, page cursor, and
reader scroll. `Ctrl-W` remains pane-local; `Esc` returns to the Work list.
