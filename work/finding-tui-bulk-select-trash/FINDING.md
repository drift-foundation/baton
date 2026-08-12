# TUI bulk selection and trash

Status: **deferred from Baton 1.1.0 to protocol 11 by Slawomir on 2026-08-12;
participant-scoped archive metadata belongs in the SQLite metastore. The
protocol-10 participant-local JSON implementation must not ship.**

## Request

Slawomir's exact release-scope request was:

> bulk select/trash needed in the next release.

This makes the feature part of the 1.1.0 release envelope. It does not yet
define whether trash is a participant-local view, a recoverable authoritative
state, or permanent authority deletion. Those have materially different
protocol, retention, audit, and compatibility consequences.

## Current behavior

**Observed:** the console has one cursor in each of the MESSAGES and Sent
views. It has no multi-selection set, selection mark, selected-count display,
range selection, or select-all command. Search is a filtered view over the
already-loaded metadata rows.

**Observed:** uppercase `D` is currently bound only to `DISCARD_DRAFT`.
`begin_discard_draft()` refuses every non-draft row, asks for confirmation for
a selected draft, and `discard_draft()` removes only that unsent draft from the
participant-local draft file. This operation never addresses the authority.

**Confirmed protocol fact:** messages are not deletable through a user-facing
trash operation. Durable message records are permanent. Transient terminal
metadata is collected by `gc` after the configured retention period; transient
content is removed by its reply/close retention transition. Notices leave
activity only through TTL, author expiry, or `gc`. Database guards restrict
message, claim, part, receipt, publication, and notice deletion to those
existing retention operations.

**Confirmed compatibility fact:** the ruled 1.1.0 release retains protocol 10
and uses existing protocol-10 authorities without a rebuild or schema
migration. An authority-level trash state or per-participant trash table would
supersede that release ruling and requires its own schema/protocol design.

## Safety boundary

Bulk selection is a presentation/input feature and can be designed without
changing authority state. Trash cannot be implemented until its lifecycle is
named. In particular:

- it must not silently turn pending or claimed directed work into invisible
  obligations;
- it must not delete durable audit/history or bypass sender-chosen transient
  retention;
- it must not reuse draft discard semantics for authority rows merely because
  both would be invoked by `D`;
- it must define whether a trashed row is recoverable and where that state is
  authoritative;
- it must define behavior for MESSAGES, Sent, notices, drafts, damaged rows,
  active claims, filtered-out rows, refresh/reordering, and rows removed by
  legitimate retention while selected.

## Proposed minimal 1.1 contract

**Proposed, not yet authorized:** make trash a recoverable,
participant-specific view state that never deletes or mutates the underlying
message/notice lifecycle. Pending or actively claimed inbound work remains
visible and cannot be trashed. Keep draft discard as its existing distinct
local destructive operation. This preserves protocol 10 and its retention and
audit contracts.

If this direction is accepted, the design still needs to choose a persistence
owner. A TUI-local file preserves protocol 10 but is device-local; authority
persistence would be consistent across clients but is a schema/protocol
change. The finding must record that choice before code changes.

## Open ruling

What does **trash** mean for 1.1.0?

1. **Recommended:** a recoverable, participant-specific hidden view that does
   not delete authority history and refuses unresolved inbound work. A
   follow-up ruling chooses TUI-local versus authority persistence.
2. Permanent authority deletion. This conflicts with the current durable
   retention/audit contract and the protocol-10/no-migration release envelope,
   so it requires an explicit supersession and broader design.
3. Bulk close/expire/GC using existing protocol verbs. These are different
   lifecycle acts, are not universally available across row types, and should
   not be labelled trash without an explicit product ruling.

## Lifecycle ruling — 2026-08-11

Slawomir clarified:

> This is about "cleaning up" the INBOX listview. This is why I earlier
> referred to it as archiving - it's about making the UX easier - if I handled
> a message I don't want to stare at it. We can retain it in full as if not
> removed more hidden. That's the feature we need

This selects the recoverable-view direction and supersedes “trash” as the
product name. **Archive changes only what the human sees in the TUI.** It never
deletes, closes, expires, collects, scrubs, changes retention, changes a claim,
or writes message/notice lifecycle state. The authority retains the row and
content exactly as if it had never been archived.

The already-confirmed 1.1 release envelope retains protocol 10, opens existing
authorities without schema migration, and treats this as an Inbox-listview UX
feature. Therefore the only compatible persistence owner is the
participant-local TUI state under that participant's configured
`projection_dir`. Authority-owned cross-device archive state would supersede
those decisions and is not 1.1 scope. The local nature must be stated in Help
and candidate trial; it must not be implied to follow the participant to
another installation.

## Implementation contract — 2026-08-11

### Views and eligibility

- Add an **Archived** view beside MESSAGES and Sent. MESSAGES omits locally
  archived identities; Archived shows those same authority-backed rows in full
  and supports the ordinary read/materialize/follow-up actions. Sent remains
  the complete authority-backed outbound view and is unaffected.
- Archive identity is `(row_type, id)`, never subject, timestamp, thread
  position, or cursor index. No content bytes are stored locally.
- Eligible received messages are those with no current reply/close obligation:
  any inbound state except `pending` or `claimed`. An inbound pending/claimed
  row, damaged or healthy, cannot be archived.
- Any outbound message is eligible because its recipient's claim is not this
  participant's obligation; it remains visible in Sent.
- A received notice is eligible only after it is seen. A notice authored by
  this participant is eligible. Unseen received notices cannot be archived.
- Drafts retain their existing separate `D` discard lifecycle and never enter
  Archived.
- Archive is row-specific, not implicitly thread-wide. Bulk selection is how a
  human archives several members of a thread. Any remaining child stays
  visible and must render safely even if its parent is archived.

### Bulk interaction

- In MESSAGES or Archived, `Space` toggles the current eligible row in a
  selection set. `Ctrl+A` selects every currently visible eligible row; a new
  arrival is never selected implicitly. Uppercase `U` clears the set.
- Lowercase `x` acts on the current row when the selection set is empty, or on
  the captured selection when it is nonempty. In MESSAGES it archives; in
  Archived it restores. The operation is recoverable local view state, so it
  needs no destructive confirmation. `D` remains draft-only.
- Selection is stored by identity and survives polling refresh/reordering.
  Changing view or changing/clearing the search query clears selection so an
  invisible row can never be acted on. An accepted unchanged filter may be
  used to select/archive its visible matches.
- Marks and the header/status show the selected count; Archived and filtered
  MESSAGES headers state both visible and archived counts. Narrow terminals
  retain a visible mark without displacing the lifecycle glyph.
- A row that vanishes through legitimate retention is dropped from the live
  selection. Eligibility is rechecked immediately before publication of local
  state; a batch is all-or-nothing, never a partial silent success.

### Local persistence

- Store a separate versioned archive-index JSON beneath `projection_dir`,
  namespaced by participant, containing only ordered/deduplicated
  `(row_type,id)` identities. Do not overload the draft file or its version.
- Use the draft store's safety class as the baseline: canonical configured
  directory, no-follow regular-file reads, bounded/validated JSON, participant
  match, scratch write, fsync, atomic replace, and directory fsync. A failed
  write leaves both the prior file and visible in-memory archive state intact.
- With no configured `projection_dir`, archive refuses honestly rather than
  becoming session-only. A missing file means an empty archive. A damaged or
  unsupported-version file is reported without touching the authority and
  disables archive mutation until corrected; do not silently reinterpret it.
- Stale identities whose authority rows later expire or are collected carry
  no content and grant no access. They may be pruned only during an explicit
  successful archive/restore write, never by a polling refresh that was
  promised read-only.

### Authority and filtering invariants

- Full public `dump()` equality must hold across select, archive, Archived
  browsing, restore, restart, search, and failed local writes.
- `wait`, claim delivery order, unresolved count, FIFO warning, held claim,
  notice receipts, retention, and GC ignore archive state. Header obligation
  counts remain unfiltered even while an owed row is visible elsewhere.
- Search remains metadata-only and filters the active MESSAGES/Archived view;
  it cannot search hidden content by reading the authority.
- Refresh reconstructs both views from current authority rows plus the local
  identity set. It never fabricates retained rows after legitimate GC/expiry.

## Acceptance boundary

Use new focused tests unless an existing assertion is case-specifically
superseded. Cover at least:

1. Space/Ctrl+A/U/x mapping, Help, marks/counts, no-selection current-row
   action, bulk archive, bulk restore, and candidate PTY use;
2. every inbound/outbound/message/notice/draft eligibility edge, including
   pending/claimed and unseen refusals;
3. identity safety across arrival, reorder, refresh, filter, view switch,
   vanished rows, duplicate message/notice ids, and thread parent/child splits;
4. local file missing/restart round trip, malformed/oversize/future-version/
   wrong-participant/symlink/non-regular cases, write/race failure, exact
   no-partial-update behavior, and no configured directory;
5. MESSAGES hides while Archived and Sent remain truthful, restore returns the
   row, search works in both list views, and narrow rendering is safe;
6. full authority dump equality, unchanged unresolved/FIFO/claim/receipt
   state, no retention bypass, and stale-id behavior after GC/expiry.

## Research and acceptance work after the ruling

- revalidate the ruled row identity and selection survival against current
  refresh, search, threading, and view code;
- revalidate the exact Space/Ctrl+A/U/x interaction, marks/counts, and
  all-or-nothing local write behavior;
- revalidate every ruled row type and lifecycle eligibility state;
- prove that bulk action addresses captured row identities, never moving
  cursor indices;
- cover mixed eligible/ineligible selections, vanished rows, damaged rows,
  active claims, unseen notices, drafts, Sent rows, filtered selection, retry,
  restart persistence, and narrow terminals;
- update the single-source key map/help and run a human TUI trial;
- independently review before the 1.1 candidate build/deploy notice.

## Search inclusion ruling — 2026-08-11

Slawomir added:

> search should include archived entries

This confirms that archiving must never make retained activity unsearchable.
The metadata-only `/` filter applies in the Archived view and archived
authority-backed rows participate there exactly as ordinary MESSAGES rows do:
author/other-party and subject only, literal `casefold()` substring matching,
no body read, claim, seen receipt, or authority write. Clearing the filter
restores the full Archived list; restoring a row returns it to MESSAGES.

This remains the already-ruled filter-in-place model: MESSAGES searches its
visible non-archived rows, Archived searches its archived rows, and Sent
searches the complete outbound view. Search does not temporarily unarchive a
row or mix archive and restore actions in one list. Candidate help and the
human soak must make the Archived-search path visible so “archive” never means
“can no longer be found.”

## Implementation-start revalidation — 2026-08-11

Immediately before delegation, the ruled contract was rechecked against the
current next-generation console. No archive index, Archived view, bulk
selection set, or Space/Ctrl+A/U/x browse event exists yet, so no partial
implementation or later code decision supersedes this finding.

The current patch boundary is concrete:

- `InboxState.refresh()` still builds the complete authority-backed
  `_all_rows`; `rows`, `sent_rows`, `_matching()`, and `view_rows` own the
  metadata-only filtered projections. Archive partitioning belongs beside
  those projections, not in authority reads.
- `VIEW_INBOX`/`VIEW_SENT`, `select_view()`, `_CURSORS`, and `_TOPS` still form
  a two-view model. Archived needs its own cursor/top and must clear bulk
  selection on view or query changes without disturbing action-target safety.
- `keys._BROWSE`, `HELP_SECTIONS`, `driver.handle_key()`, `render._header()`,
  and the list-pane renderers remain the single-source key/dispatch/help/count
  surfaces. Space, Ctrl+A, `U`, and `x` are unbound in browse mode.
- `drafts.py` still supplies the required no-follow, private, validated,
  scratch-write/fsync/replace/directory-fsync safety class. Archive persistence
  must be a separate versioned participant file/module and must not overload or
  migrate draft format 3.
- Search remains `row_matches()` over active-view metadata and performs no
  content read. The same predicate can govern Archived after the backing rows
  are partitioned by `(row_type,id)`.

Slawomir's repository-policy ruling in message
`c34b344061243c5a8d66af82338b04eb` supersedes the acceptance-boundary wording
that required case-specific permission for additive existing-test coverage.
New tests and additive cases or exhaustive-registry members are always
authorized; changing or weakening an existing expectation still is not.

This is now the sole serial implementation item delegated to
`baton.implementer`. K owns source, tests, and a new `PROGRESS.md`; the reviewer
retains FINDING/PLAN/review-journal ownership. Frozen 1.0 artifacts/manifests,
the live authority/config, candidate deployment/activation, and Git state stay
out of scope.

## First implementation review — 2026-08-12

The initial implementation is **changes requested** in
`review-2026-08-12T00-02-57Z.md`. The new store, key/help/render surface, core
eligibility predicate, identity-keyed selection, authority isolation, and most
focused coverage are substantial, but the pass does not yet meet the pinned
wrong-target, unresolved-work, active-view, or all-or-nothing boundaries.

Most critically, view-generic selection was added without converting the
existing MESSAGES-only commit paths: switching to Archived can claim and open
a different pending row that is hidden in MESSAGES. A structurally valid local
index can also name and hide a pending/claimed message or unseen notice because
partitioning trusts identity membership without rechecking eligibility.

The shared `select` affordance also makes `Ctrl+A` depend on whether the current
row is eligible. Independent execution of K's own focused/PTY set therefore
produced 74 passes and two failures; same-second id ordering can hide or expose
the bug. Five additional boundary probes all failed: wrong-target Archived
entry, unresolved work hidden by a valid index, Archived cursor stranded by a
filter, non-private index acceptance, and post-replace fsync failure leaving
disk changed while reporting failure/keeping memory unchanged.

Bulk archive remains the sole serial item. No candidate build/deploy gate may
advance until the correction pass and independent re-review close.

## SQLite ownership and protocol-11 deferral ruling — 2026-08-12

Slawomir ruled that SQLite is Baton's metastore and should own archive state.
Archiving is therefore postponed until protocol 11, whose schema change can
add participant-scoped archive metadata deliberately. It remains presentation
metadata, separate from delivery lifecycle: archive/restore must not close,
delete, acknowledge, expire, collect, change retention, change a claim, or
otherwise alter a message or notice.

This **explicitly supersedes** all earlier text that made bulk archive required
for 1.1.0 or made a participant-local JSON file under `projection_dir` its
persistence owner. The 2026-08-11 lifecycle, interaction, search, eligibility,
and safety work remains chronological design evidence for protocol 11, but it
is not an implementation contract for protocol 10 and must be revalidated
against the protocol-11 schema and operations before later implementation.

The current JSON archive implementation and its 1.1-only UI/help/tests must be
withdrawn from the 1.1 release candidate. That withdrawal is the remaining
work for this serial item; the two correction rounds are not a reason to keep
or finish a storage design whose ownership has been overruled. Shared changes
that belong to independently approved 1.1 features must be preserved, and the
withdrawal must be verified without touching frozen artifacts, live authority
or config, deployment, or Git state.

Once that scoped withdrawal and the included-finding reconciliation are
reviewed, the 1.1 candidate may proceed directly to Slawomir's human build,
testing, and RC phase. Bulk archive is no longer a 1.1 soak or release gate.
