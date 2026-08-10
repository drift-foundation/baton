# Enter from the message list enters DETAIL

Status: **ruled; implementation in progress**.

Parent: `work/finding-human-console/`.

Discovery context: live TUI use showed that opening/claiming a message did not
move navigation into its body; the human still had to press Tab before Vim
scroll keys acted on DETAIL.

## History and supersession

Slawomir had agreed that Enter should “enter the message” so body navigation
works without first pressing Tab. That decision was never recorded. The later
focus plan explicitly said Enter kept its old semantics, and the
implementation correctly followed the wrong written rule. This lost decision
is the incident behind `AGENTS.md` § “Confirmed decisions are pinned before
implementation.”

This finding supersedes only the old statement that Enter does not route
through focus. `Tab`/`Shift-Tab` remain the general reversible focus toggle.

## Required contract

- In browse mode with LIST focus, Enter enters/focuses DETAIL for the selected
  row, analogous to the forward direction of Tab.
- On a pending inbound directed row whose two-second dwell has not completed,
  Enter is an explicit commit: claim and open that exact message immediately,
  then focus DETAIL. It never redirects to the FIFO head or a neighbour.
- On an already-claimed/open row, reopen or retain its detail and focus it
  without another claim.
- On handled and outbound rows, open/retain their authorized read-only detail
  and focus it without an authority write.
- On an unseen notice, Enter keeps its atomic mark-seen/open action and then
  focuses DETAIL. On a seen notice it focuses only what the console may
  lawfully show and creates no second receipt or invented redelivery.
- Enter from DETAIL does not toggle back to LIST. Tab/Shift-Tab remain the
  return path.
- Draft reopening, pickers, compose/reply editing, send confirmation, and all
  other modal Enter semantics remain unchanged.
- An empty/detail-less selection fails visibly and creates no focusable
  phantom content.

Focus itself remains pure UI state. Only the pre-existing open/claim/see action
may write authority state.

## Required evidence

1. Enter before dwell expiry claims exactly the selected directed message and
   focuses DETAIL.
2. Already-open, handled, and outbound rows focus without a second claim or
   write.
3. Unseen notice produces exactly one receipt and DETAIL focus; seen notice
   produces no second receipt.
4. Enter from DETAIL does not return to LIST.
5. Compose, reply, confirmation, picker, draft, and empty-list cases preserve
   their semantics.
6. Context-sensitive help/README describe the one-way shortcut.
7. Packaged PTY coverage proves the real key reaches the same behavior.
