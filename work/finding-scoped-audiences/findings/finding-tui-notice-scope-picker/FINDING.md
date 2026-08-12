# TUI cannot choose a scoped notice audience

Parent: `work/finding-scoped-audiences/`

Status: **implemented and reviewer-signed-off 2026-08-11 after the retained
audience and cross-version draft-format defects were repaired.**

Reported by Slawomir on 2026-08-11: “right now it's impossible to address the
team (`lang.*`) when creating a notice.”

## Observed

The authority and agent CLI already support a frozen team audience:

    send-notice --scope 'lang.*'

The human console does not. `N` calls `InboxState.begin_compose(notice=True)`,
which enters `MODE_NOTICE` immediately. `NOTICE_FIELDS` contains only
`subject`, the compose screen shows no audience, and `send_compose` calls
`Store.send_notice` without `scope`. Every TUI-authored notice is therefore a
global notice to everyone.

This is not a missing scoped-broadcast protocol capability. It is an omitted
authoring path in the TUI. The parent originally pinned global and configured
team scopes without a free-form path; that closed-picker UX was superseded by
Slawomir on 2026-08-11 below.

## Confirmed contract inherited from the parent

- A scoped notice uses a dotted complete-segment selector ending in literal
  `.*`; `lang.*` includes deeper `lang.a.b` addresses but not `lang_extra.x`.
- Scope expansion is validated and frozen by the core in the publication
  transaction. The TUI supplies the selected scope; it never expands or
  authorizes the audience itself.
- Global remains available and explicit. It freezes the full configured
  participant set at publication exactly as it does today.
- **Superseded 2026-08-11:** the selector was to be chosen only from scopes
  derived from the configured participant registry, not typed as text. The
  current ruling is an editable, filtering control with manual scope entry.
- Choosing, paging, cancelling, editing, and confirming are local UI actions
  and write nothing to the authority. Only confirmed send publishes.
- A scope that becomes invalid or empty after selection is refused by the core;
  the complete draft and chosen audience remain available for correction.

## Confirmed UX supersession — 2026-08-11

Slawomir rejected an exhaustive team-scope drop-box. The audience control must
behave like a searchable, editable combobox:

- as the human types `web`, the suggestion area narrows to configured matching
  team scopes instead of listing every team all the time;
- the typed text remains an input, not merely a filter over fixed rows;
- typing the complete valid scope `web.*` and confirming publishes that scoped
  broadcast even if no precomputed suggestion was chosen;
- global remains an explicit visible `*` choice/value;
- invalid or empty scopes are refused by the core with the whole draft and
  typed audience preserved.

## Exact audience ruling — 2026-08-11

The semantic edge above is **resolved**. Slawomir ruled that notices are for
teams. The control presents and accepts only:

    *
    team-a.*
    team-b.*
    …

`*` is the TUI spelling for the existing global notice (`scope=None`);
`team-a.*` is passed unchanged as the core scope. Exact participants never
appear in the list and no exact-participant notice is added. Typing `team`
filters the team-scope options just as the ordinary send picker filters
recipients, but this control remains team-oriented.

## Recommended patch boundary

**Proposed:** make `N` open the ruled audience combobox before notice
composition. The control offers explicit `*`, filters registry-derived
team-scope suggestions as text is typed, and accepts a complete manually typed
scope. A confirmed value enters the existing notice composer with the explicit
audience held separately from subject/body text.

The implementation may generalize the existing recipient picker or add a
notice-audience picker mode. Whichever shape is used, the picker purpose must be
explicit so selecting `lang.*` cannot accidentally enter directed compose, and
ordinary recipient selection cannot accept a wildcard.

Required code paths:

- `src/baton_tui/state.py`: picker state/entries, notice compose state,
  `send_compose`, retained-draft snapshot and reopen;
- `src/baton_tui/driver.py` and `src/baton_tui/keys.py`: `N`, picker dispatch,
  cancel/page/select, and help vocabulary;
- `src/baton_tui/render.py`: picker rows and an always-visible chosen audience
  in compose and confirmation;
- TUI state/driver/render/PTY tests. Core scope semantics do not change.

## Acceptance boundaries

1. `N` offers explicit `*`; typing `lang` filters matching configured team
   scopes, and typing/confirming `lang.*` supplies that scope without requiring
   a drop-box selection. Exact participant addresses never appear.
2. A scoped TUI notice reaches every and only the core-expanded `lang.*`
   audience. An unrelated team neither wakes nor records a receipt.
3. A global TUI notice keeps current behavior, but the confirmation shows `*`
   before publication.
4. The selected audience survives field changes, external-body editing,
   confirmation decline, draft retention, restart/reopen, and send failure.
5. Picker open/page/cancel and confirmation decline produce a byte-identical
   authority dump; cancellation publishes nothing.
6. Suggestions are deterministic, deduplicated, filtered incrementally, and
   usable at narrow terminal sizes without becoming an exhaustive scope list;
   manually entered scopes are not rejected merely because no suggestion row
   was precomputed.
7. A participant/config change between selection and send fails visibly through
   core validation and preserves the draft; the TUI does not publish globally
   as a fallback.
8. Existing directed-recipient picker, global/scoped rendering, at-most-once
   receipt, and query-to-arm wake behavior remain unchanged.
9. Released 1.0.0 binaries/manifests and the production authority/config remain
   untouched; implementation belongs in the next-generation workspace and
   candidate build, never the released artifacts.

## Open

No product boundary remains open. Exact visual grouping and whether the
existing picker is generalized are implementation details to revalidate
against the current TUI model.

## Implementation review — 2026-08-11T15-29-59Z

**Observed, blocking:** the selected scope is not part of `_draft_from_state`,
the version-1 draft schema does not accept or validate it, and `reopen_draft`
does not restore it. A minimal restart/reopen probe retained a notice addressed
to `web.*` and reopened it with `notice_scope is None`. `send_compose` maps
`None` to the global protocol spelling, so sending that reopened draft would
broadcast to everyone. This violates acceptance 4 and creates exactly the
wrong-audience fallback acceptance 7 forbids.

**Observed:** a successful scoped send still reports `to everyone (notice)`.
The authority operation is scoped, but the console's success report says it
was global.

**Observed:** the new tests cover in-session confirmation decline and core
refusal, but not retained-draft restart/reopen or external-body editing. The
chosen audience also is not explicitly cleared at completion/cancellation
boundaries, leaving stale state outside the compose buffers. Those lifecycle
boundaries need regressions along with the persistence repair.

The full review is
`review-2026-08-11T15-29-59Z.md`. Current outcome: **changes requested**.

## Implementation review 2 — 2026-08-11T15-45-24Z

**Confirmed fixed in the current source:** the scope now survives retain,
restart, reopen, external editing, confirmation, and send; legacy scope-less
drafts become explicit global drafts; success names the true audience; cleanup
is explicit. The focused 27-test suite, draft suite, core API suite, and all
1,652 TUI tests pass independently.

**Observed, blocking:** the safety-critical audience field is still written
with draft document `version: 1`. The frozen 1.0 console accepts that version,
ignores the unknown `notice_scope` field, reopens the draft as an ordinary
notice, and its publication call supplies no scope. A scoped draft written by
1.1 and later opened after a rollback to 1.0 can therefore broadcast globally.
The frozen artifact was exercised directly and produced a reopened notice with
the correct subject but no `notice_scope` state.

The new writer needs a forward-incompatible draft format version. The new
reader should explicitly migrate historical version-1 notice drafts to global
`*`, while version 2 requires an audience on every notice draft. That makes the
frozen version-1 reader refuse the newer file instead of silently changing its
meaning. Full details are in `review-2026-08-11T15-45-24Z.md`. Current outcome:
**changes requested**.

## Implementation review 3 — 2026-08-11T15-55-03Z

**Confirmed fixed and signed off:** the current console writes draft format
version 2 and reads versions 1 and 2. Historical version-1 notice drafts are
migrated in memory to explicit global `*`; experimental version-1 drafts that
already carry an audience preserve and validate it; version-2 notice drafts
require a nonempty audience. The frozen 1.0 console now refuses the version-2
file instead of reopening a scoped notice as global.

The final independent run passed all 1,655 TUI tests; the focused scope/draft
run passed 70 tests; `git diff --check` passed; and the released binaries remain
unchanged. Full review: `review-2026-08-11T15-55-03Z.md`. Current outcome:
**approved**.
