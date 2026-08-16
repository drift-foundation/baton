# Incoming work is bold until handled

Status: **implemented, independently approved, confirmed by human zipapp trial, and final release gate passed; awaiting RC commit**.

Human trial note: Slawomir confirmed on 2026-08-10 that the current packaged
TUI visibly bolds an incoming subject. Formal implementation handoff and
independent coverage review remain pending, including claimed/handled and
unseen/seen transitions.

Parent: `work/records/2026/08/finding-human-console/`.

Discovery context: during the final RC trial, Slawomir observed that incoming
work does not stand out from retained history. He ruled that the message list
should use the familiar unread-email convention: work still owed by the local
participant is bold.

## Confirmed interaction

- An incoming directed message is bold while the local participant still owes
  its terminal action: reply or close. This includes both pending and locally
  claimed/open directed messages.
- An unseen notice is bold. After the local participant sees it, the retained
  notice row is normal weight.
- A directed message becomes normal weight immediately after the local
  participant replies or closes it.
- Outbound messages, already handled incoming messages, and seen notices are
  not bold under this rule. Their existing direction and completion glyphs
  continue to carry their own meanings.
- Bold is a presentation of the existing local obligation/receipt state, not a
  new protocol state and not a claim trigger. Rendering or refreshing it must
  not write to the authority.
- Selection/focus highlighting and bold must compose: moving the cursor over
  an owed row must not make the unread emphasis disappear.
- The rule applies consistently to the source TUI and packaged `bin/baton-tui`.

## Required evidence

1. Pending incoming directed rows render bold.
2. Claimed incoming directed rows remain bold until reply/close.
3. Replied and closed incoming rows render normal weight.
4. Unseen notices render bold and retained seen notices render normal weight.
5. Outbound rows are unaffected.
6. The selected-row style preserves the bold bit while applying its highlight.
7. Rendering/refresh performs no claim, see, or other store mutation.
8. A packaged PTY regression observes the attribute transition on the rebuilt
   zipapp, or an equivalent packaged-boundary assertion proves the exact
   source renderer is present when terminal attributes cannot be inspected
   portably.

No protocol, schema, CLI, core, delivery, claim, or receipt change is
authorized by this finding.

## Resolution

Approved by `baton.reviewer` on 2026-08-11 after independent rule, real-row,
no-write, selection-composition, packaged PTY, artifact, and whitespace checks.
Slawomir confirmed the incoming-subject emphasis in the packaged TUI. The final
gate then passed 2318 tests, deterministic rebuild, packaged workflow smoke,
and live doctor. The reviewed RC commit remains.
