# Make pane-focus navigation immediate and discoverable

## Observed — 2026-08-20

The Work-detail Threads/Message-index/reader screen implements the previously
approved geometric `Ctrl-W` direction model, but a human must pause between
`Ctrl-W` and `j`/`k`. Entering the chord at normal Vim speed is unreliable and
makes the navigation feel glitchy.

Top-level TUI tabs now use the consistent `[` / `]` grammar. That frees normal
view-mode `Tab` and `Shift-Tab` to offer a more discoverable pane-focus cycle
for users who do not use Vim window commands.

This follows the earlier permanent decision at
`work/records/2026/08/finding-recursive-target-graph/findings/`
`finding-tui-message-index-body-layout/findings/`
`finding-message-pane-navigation/`; it does not replace its geometric mapping.

## Confirmed decision

- Keep `[` / `]` as the only navigation between top-level and nested tabs.
- Keep `Ctrl-W` plus `h`/`j`/`k`/`l` and arrow directions as geometric
  pane-focus navigation. The second key must be accepted immediately at normal
  chord speed; no deliberate pause between keys is part of the interaction.
- In ordinary detail view, `Tab` cycles focus forward through the visible
  regions and `Shift-Tab` cycles backward.
- `Tab` and `Shift-Tab` no longer switch top-level tabs. `[` / `]` are the
  exclusive previous/next-tab gestures at both tab levels; outside detail
  view, Tab is inert unless the current text-entry context owns it.
- Context-specific Tab behavior remains authoritative while editing: command
  mode keeps completion/history adoption, and no text-entry surface loses its
  existing Tab contract to pane navigation.
- Focus movement remains read-only and never changes selection, seen state, or
  authority data.

## Acceptance boundary

- Before implementation, the implementer records a successful reproduction of
  the required pause through a real terminal/PTY or names the exact input-state
  transition that delays an immediate second key. Failure to reproduce returns
  the Work for more evidence; it does not authorize a speculative timing fix.
- Raw PTY input for immediate `Ctrl-W j` and `Ctrl-W k` moves exactly once and
  does not require sleeps inserted between the bytes.
- Repeated `Tab` and `Shift-Tab` visit every currently visible region in stable
  forward/reverse order and wrap deterministically.
- Wide and narrow layouts use the same logical focus states even when their
  geometry differs.
- `[` / `]` continue to switch tabs and never move pane focus.
- Command, search, batch, editor, and other text-entry modes retain their
  established Tab/Shift-Tab semantics or explicitly refuse where none exists.
- Footer/help text advertises both the Vim chord and Tab alternatives without
  consuming an extra permanent row.

## Mandatory-gate result — 2026-08-20

The implementer ran the gate before editing and could not reproduce the
reported pause. The retained `evidence/chord-probe.py` drives a real PTY and
confirms immediate one-write `Ctrl-W j`/`k`, CSI and SS3 arrow variants,
multiple rapid chords, a detail-open plus chord in one write, a 120 ms
separation, and a 2.6 second separation crossing the refresh deadline. Every
case preserves the prefix and moves focus according to the current geometric
map. No product code or tests were changed.

That result does not disprove the live report: the PTY probe cannot reproduce
the operator's terminal emulator, multiplexer, or keyboard protocol. Before a
timing/input fix may proceed, collect the live `TERM`, multiplexer state,
whether `j`/`k` and arrow forms both fail, whether Messages and Events both
exhibit it, and preferably a raw-key or terminal recording. Until then the
timing half is evidence-blocked, not resolved.

## Scope ruling — 2026-08-20

The approver dropped further pursuit of the `Ctrl-W` pause in this Work. The
existing geometric `Ctrl-W` navigation remains unchanged; W1151 neither claims
to fix nor disprove the live observation. If it becomes worth pursuing again,
a new finding starts from the retained PTY evidence plus a fresh live-terminal
capture.

This ruling supersedes the `Ctrl-W` implementation and reproduction acceptance
items above for W1151. Its remaining deliverable is only the confirmed
secondary pane-navigation method: view-mode `Tab` cycles forward and
`Shift-Tab` cycles backward, while `[` / `]` remain the exclusive tab-switching
keys and text-entry contexts keep their own Tab contracts.
