# TUI correction — return focus to Messages after disposition

**Status:** confirmed UX requirement, reported by Slawomir during packaged
TUI testing on 2026-08-09.

## Observed behavior

After closing a message, the TUI leaves keyboard focus in the Detail pane.
The disposed message no longer needs an action, so the user must press `Tab`
before continuing through the queue.

## Required behavior

After any successful terminal disposition initiated from the TUI—at minimum
`close`, and consistently after a successful reply—the application must:

1. refresh the Messages view and row state;
2. move focus to the Messages pane;
3. preserve the selected row by identity after refresh, matching the standing
   trial ruling; pane focus changes, cursor identity does not;
4. make normal Messages navigation available immediately, without an extra
   `Tab` keystroke.

Failure or cancellation must not move focus as though the disposition
succeeded. The packaged zipapp is the acceptance surface because that is the
artifact Slawomir tests.

## Reviewer correction

The first draft said to prefer the next actionable row. Slawomir's report only
asked that closing return pane focus to Messages; it did not ask the cursor to
advance. That extra behavior was an unsupported reviewer inference and
contradicted the existing trial pin that preserves selected-row identity after
a successful send. It is withdrawn. The shared success tail implemented by K
is the intended contract: focus returns to Messages, the answered/closed row
stays selected, and the next navigation key acts on the list immediately.
