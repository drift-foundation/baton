# Finding: Messages view exposes unrelated Work actions

## Observed — 2026-08-17

The v11 Work-details Messages surface renders `can: prioritize` in its facts block. `prioritize` is a canonical capability of the selected Work: any configured member of the Work's owning team may change its priority. It is not a capability of the selected Thread or Message.

The label is therefore misleading in the Messages view. A reader can reasonably interpret it as a message operation even though the projection is describing Work authority.

## Confirmed ruling — 2026-08-17

**Approved by Slawomir during the live v11 trial.** Remove `can: prioritize` from the Messages surface entirely. Message reading must show message-, Thread-, and reading-context facts only; it must not repeat unrelated Work mutation capabilities.

This does not remove `prioritize` from the protocol, JSON detail projection, command grammar, or a genuine Work-actions/help surface. It changes only what the human Messages view renders. No authority schema or projection change is required.

## Acceptance boundary

- A participant who may prioritize the selected Work does not see `can: prioritize` while reading its Threads and Messages.
- Message navigation, bodies, references, new/seen state, and contextual commands remain unchanged.
- The canonical JSON `available_transitions` value remains available to clients.
- Source and packaged TUI behavior agree at wide and narrow widths.

## Revalidation — 2026-08-17 after W76

The defect remains present after the message-pane redesign.
`src/baton_work/tui/app.py::_facts()` appends `available_transitions` as a
`can: ...` fact, and `_render_detail()` paints that fact block immediately
above Threads. `_facts()` is the only production renderer of that text; the
canonical projection and command grammar need no change.

The narrow implementation boundary is to stop the Messages/Work-detail facts
from rendering Work transition capabilities while preserving outcome,
claimant, binding, contract revision, duplicate, and follow-up facts. Focused
tests should exercise `_facts()` for both an authorized and unauthorized
viewer, then prove source and packaged wide/narrow screens omit `can:` without
losing Threads, Messages, bindings, or terminal rationale.
