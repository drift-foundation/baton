# Finding: organize the v11 TUI around Jobs, Teams, and Inbox

## Context — 2026-08-18

The v11 TUI currently opens directly on Work and uses the persistent header
for participant-relative `oblig`, `park`, and `due` counters. Conversational
pokes introduced another owed-action class, and the first projection-12 smoke
showed that a human could be addressed without the TUI making that action
discoverable. The existing header no longer scales into a coherent operating
surface.

The narrow correction for pending-poke visibility remains owned by
`work/records/2026/08/finding-tui-poke-visibility/`. This record owns the
broader navigation and information architecture; it must not expand or rewrite
that in-flight Work.

## Confirmed navigation model — 2026-08-18

The main TUI has three top-level tabs:

    [Jobs] [Teams] [Inbox total/unseen]                         baton.slaw

- Tabs are left aligned and are the first content in the header.
- The current participant identity is right aligned on the same line.
- The former `[oblig] [park] [due]` header counters are removed. Obligations
  and due trials belong in Inbox; parked Work remains visible and filterable
  in Jobs. Duplicating those facts in the global header is noise.
- The selected tab is visually distinct. The tab model must remain usable at
  narrow terminal widths without silently hiding owed action.

## Jobs

Jobs is the current Work tree and Work-detail experience. It retains Work
filtering, containment, Messages, and Events. This change does not redefine
Work workflow authority.

## Teams

Teams provides an operational roster rather than another Work queue:

- browse configured teams and their members;
- show each member's display name, roles, route coverage, canonical claimed
  Work/current activity, and latest reported runner status when available;
- default to the viewer's own team to reduce noise, while permitting deliberate
  navigation into every configured team;
- allow a participant to poke one selected member and inspect the raw,
  structured reply, including provider/model/session/auth/limit fields when
  the member reports them.

Teams never guesses liveness from a process table or a stale TUI session. Its
workflow facts come from the Baton authority and its runner facts come from
the poke answer.

### Follow-up clarification — 2026-08-19

The final sentence above remains W25's implementation boundary but is
superseded for the later W93 runtime-state release. W25 delivers the roster and
last on-demand poke answer without taking on another schema or adapter change.
`work/records/2026/08/finding-agent-runtime-state/` subsequently adds a
distinct leased runner-state authority, Jobs `Agent` column, and richer Member
details. The poke answer remains a separate on-demand agent report; W93 does
not reinterpret it as live state.

## Inbox

Inbox is the participant-relative action and attention surface. It includes:

- pending conversational pokes addressed to the participant;
- pending `@` obligations owed through a route the participant handles;
- due verification trials handled by the participant's route;
- directed Topic/Message attention that the authority projects for the
  participant.

Inbox does not create a second free-floating direct-message system. Messages
remain in their Topics and retain their Work context; Inbox rows link to that
context. Pokes remain the lightweight context-free status exchange.

The Inbox tab label displays `total/unseen`. `total` is the number of rows in
the current participant's Inbox and `unseen` is the subset not yet seen by
that participant. The whole Inbox tab is bold whenever at least one row is an
unresolved action the current participant owes, even when that row has
already been seen. Seen state therefore never hides that the viewer is the
blocker.

Rows visibly distinguish attention-only items from owed actions and identify
their type. The participant can open the canonical Topic, Work, obligation,
trial, or poke directly and perform the corresponding supported action without
copying raw ids from JSON.

## Interface parity

The TUI is one projection of the model, not its only interface. CLI/JSON must
expose enough typed, participant-relative data for an agent to derive the same
Jobs, Teams, Inbox counts, owed-action cue, navigation targets, and allowed
actions. Glyphs, bold text, and tab placement are presentation only; JSON uses
explicit fields.

## Acceptance boundary

- Preserve W17's narrow pending-poke correction and integrate it rather than
  duplicating its authority reads.
- Add focused tests for tab order, selected-tab navigation, right-aligned
  identity, narrow-width behavior, and removal of the legacy header counters.
- Cover Inbox `total/unseen`, seen-but-still-owed bolding, no-action unbolding,
  mixed poke/obligation/trial/message rows, and contextual navigation.
- Cover Teams own-team default, cross-team browsing, roles/routes, canonical
  claim display, poke initiation, and raw structured answer inspection.
- Cover CLI/JSON parity for every semantic field rendered by the TUI.
- Do not infer authority state from the filesystem, process table, or UI-local
  state.
