# TUI correction — simplify pane headers

**Status:** confirmed UX requirement from Slawomir's packaged TUI trial on
2026-08-09.

## Top pane

Replace the current identity-plus-pane-label header:

```text
human.slawomir  > MESSAGES  [109 retained, 0 awaiting your reply/close]
```

with the direct queue summary:

```text
Messages: 109 retained, 0 awaiting your reply/close
```

The count is the useful information. The product, participant, pane name in
all caps, focus marker, and brackets should not compete with it on this line.

## Bottom pane

Remove the literal `DETAIL`/`DETAILS` label. The lower pane is self-evidently
the selected message's detail area; naming it adds noise without information.

Show the participant identity in the lower header/status area instead,
right-aligned when the available terminal width permits. Narrow layouts must
degrade safely—truncate or omit the decorative identity before corrupting the
message display or status text.

## Focus

This does not revoke the focus/navigation contract. The UI may retain a
subtle style or marker that distinguishes list focus from detail focus, but it
must not restore the removed `MESSAGES`/`DETAIL` labels or add explanatory
mid-screen text. Keyboard behavior remains the authority: list focus makes
navigation move rows; detail focus makes navigation scroll the message.

Pin source rendering and the packaged zipapp at normal and narrow widths.
