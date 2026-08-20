# Finding: use one bracketed tab grammar throughout the TUI

## Status

Confirmed by Slawomir on 2026-08-19 and ready for implementation.

## Observed

The TUI currently teaches two different gestures and two different visual
grammars for the same concept:

- top-level Jobs, Teams, and Inbox use `Tab`/`Shift-Tab`, and only the active
  label is bracketed; and
- Work detail's Messages and Events use `[`/`]`, again with only the active
  label bracketed.

The top-level implementation deliberately avoided `[`/`]` because Work detail
already used them. That distinction is counterproductive: the keys perform the
same semantic operation at two contextual levels, so reuse makes tab
navigation consistent rather than ambiguous.

This finding supersedes the top-level navigation and rendering rule in
`work/records/2026/08/finding-tui-jobs-teams-inbox/` that assigns top-level tab
movement only to `Tab`/`Shift-Tab` and uses brackets as the active-tab cue.
It does not supersede that record's Jobs/Teams/Inbox information architecture.

## Confirmed decision — 2026-08-19

- Every visible tab label is enclosed in square brackets. Examples:

      [Jobs] [Teams] [Inbox 3/1]
      [Messages] [Events]

- The active tab is highlighted. Brackets identify controls as tabs; they do
  not by themselves identify which tab is active.
- `[` selects the previous tab and `]` selects the next tab at the current
  view level, with wrap-around:
  - top level: Jobs, Teams, Inbox;
  - Work detail: Messages, Events.
- `Tab` and `Shift-Tab` may remain compatibility aliases for top-level tab
  movement, but `[`/`]` are the canonical documented tab-navigation keys.
- `Ctrl-W` remains pane navigation. Tab movement must not change pane focus.
- Text-entry modes keep `[` and `]` as literal input; the navigation binding
  applies only where the TUI is interpreting view-navigation keys.

## Acceptance boundary

- Top-level and Work-detail tab bars bracket every tab and highlight exactly
  one active tab.
- `[`/`]` move backward/forward at both tab levels from every applicable pane,
  including wrap-around, without leaking from Work detail to the top level.
- `Ctrl-W` pane movement and command/text entry retain their current behavior.
- Narrow layouts preserve an unambiguous active tab and do not partially paint
  a bracketed label.
- Focused virtual-screen and real-terminal regressions cover rendering,
  navigation, context separation, aliases, literal command input, and narrow
  widths.
- Operator documentation and footer hints teach the same canonical keys and
  visual grammar.
