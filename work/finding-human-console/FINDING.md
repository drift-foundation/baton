# Baton needs a human-oriented console

Folder: `work/finding-human-console/`
Status: protocol-9 TUI+core stage implemented and review-approved. Markdown
rendering is deferred to `work/finding-tui-markdown-rendering/`; CLI adoption
is a separately landed next stage.

> Refreshed 2026-08-07 for the shipped protocol. The seed-based identity model
> and the protocol-7 sequencing this finding originally assumed are both
> obsolete: a participant address is now the whole identity, and the typed
> content envelope has landed. Product acceptance criteria are unchanged.
Priority: **#1 immediately after the post-cutover cleanup review closes.**
Raised by: Slawomir, 2026-08-07, while the wait/notice delivery work was in flight.

## Problem

Raw Baton JSON is an appropriate machine protocol but a poor human interface.
Reading and responding from a terminal exposes transport details -- base64
payloads, manifest digests, part trees -- and makes claim lifecycle actions
easy to get wrong.

## Required direction

Provide a console or UI that:

- presents readable message parts;
- hides base64 payloads and integrity metadata by default;
- shows pending and claimed state clearly;
- provides explicit wait/inbox, reply, close, notice, and attachment actions;
- makes it clear when a consumed directed message still requires `reply` or
  `close`.

## Authority and safety constraint

The console must use Baton's transactional API. It must never read or mutate
the SQLite authority as an alternative protocol path. Direct database writes
can violate claim and receipt invariants and are treated as corruption by
`doctor`.

## Pinned architecture

There are three components and one implementation of Baton semantics:

    baton-core
    ├── baton       agent-oriented CLI
    └── baton-tui   human-oriented terminal UI

- `baton-core` is an importable shared package and the sole owner of protocol,
  schema, validation, storage, claim, reply, notice, attachment and audit
  behaviour. SQLite is private to this package.
- `baton` remains the small, stable agent-to-agent CLI. Its distribution
  contains the core and CLI adapter only: no TUI modules, terminal framework,
  rendering code or TUI dependency may enter the CLI artifact or import graph.
- `baton-tui` is a separate executable/distribution with its own application
  version and release cadence. It calls the SAME public core API directly; it
  does not copy protocol logic, read SQLite, or shell out to the JSON CLI as
  its normal implementation path.
- Core/protocol compatibility is explicit. UI-only work does not change the
  protocol, and a faster TUI release must declare which core API it supports.
- There is one source implementation. Independently built artifacts may
  package that shared source for standalone deployment, but there must never
  be a forked CLI implementation and TUI implementation of the same rule.

The migration may contain TWO implementations temporarily, by explicit
sequencing decision: create `baton-core` from a copy of the current Baton,
leave the existing CLI implementation frozen, and build/prove the TUI against
the new core before changing the agent CLI. This duplication is scaffolding,
not an accepted final state. Differential parity checks must cover it, no
feature is implemented independently in both copies, and the old
implementation is deleted when the CLI moves to the shared core.

“Frozen” is absolute: the old CLI implementation is a read-only parity oracle
throughout the scaffold period. A defect discovered during extraction is
fixed in core only and recorded as an intentional differential result; editing
both copies until they agree would destroy the evidence the oracle exists to
provide.

The packaging refactor itself must preserve CLI behaviour and standalone
operation. The built `baton` artifact must be inspected by a regression that
proves it contains no TUI code or dependency; TUI support is not a reason for
the agent CLI to grow.

The source hash in `DISTRIBUTION.json` must become a deterministic digest of
the core source tree (sorted relative paths with path and content in the
digest), because one pinned `baton_v6.py` no longer represents the source.
The artifact digest remains the digest of the built executable.

## Pinned TUI interaction

The primary environment is an SSH terminal. The UI is keyboard-first and has
two panes, STACKED — not columns:

    MESSAGES: status, other party, subject, date       (full width, ~40%)
    ────────────────────────────────────────────────────────────────────
    Selected message / readable part / draft           (full width, ~60%)
    Status: latest asynchronous event, success, warning or error

The panes are separated by ONE continuous Unicode box-drawing horizontal rule
`─` (U+2500) spanning the full terminal width, with ASCII `-` only as a
rendering fallback. The rule occupies one row and stays unbroken through
redraws, row highlighting and terminal resizing.

The default pane allocation is 40% list and 60% detail of the body HEIGHT,
after reserving the one-row rule. One shared layout helper owns that ratio for
rendering, scroll counts, cursor placement and resize handling, so a later
configurable ratio has one contract surface rather than duplicated arithmetic.
There is deliberately no pane-WIDTH helper: both panes are the whole terminal
width, and a surviving 40/60 column split would be a second authority saying
otherwise.

**Superseded, do not restore:** side-by-side columns with a vertical `│`
(U+2502) divider, a 40%-wide inbox column beside a 60%-wide detail column, and
a highlight span that had to stop before the divider's column. The two things
a console shows are a one-line subject and a Markdown body; both want width,
and splitting the terminal gave each of them a little over half of what it
needed. Height is the cheaper axis to divide, because a list is scrollable and
a body is scrollable and a truncated line is neither.

- The inbox shows the FULL pending and active-claim queue, not one message at
  a time. It is populated through a non-claiming `scan`/poll API; it must not
  use directed `wait`, because `wait` would claim the oldest message before
  the human chose it. Fixed-interval `scan` is an acceptable first mechanism,
  but the core may add a wakeup-aware non-claiming poll so the UI need not
  trade latency against needless queries.
- **NEWEST FIRST is the default order**, by the total order `(created_ts,
  id)` descending -- Slawomir's ruling. MESSAGES is retained activity, so with
  oldest-first reaching new work meant scrolling past the entire history and
  that cost grows forever. New at top makes new work constant-time to reach
  and leaves history below it.

  This is PRESENTATION ONLY. Authority delivery is unchanged and still FIFO:
  `claim` and `wait` take the oldest pending message, and the console never
  uses them to populate the list. The two orders are exact reverses of each
  other, which is the property to pin -- if they tie-broke differently, "the
  newest message" and "the one `claim` takes last" would be different rows.

  Choosing a later message remains possible across teams; choosing one while
  an earlier message from the same sender/thread is pending warns rather than
  forbids. That comparison is by `(created_ts, id)`, NEVER by position in the
  list: position meant "older" only while the list was oldest-first, and under
  this ruling it silently means the opposite.

  An arrival lands at the TOP and shifts every row down, so the selection is
  preserved by ROW IDENTITY across a refresh rather than by index. A numeric
  cursor would quietly point at a different message and the next Enter would
  claim something nobody chose -- the wrong-target bug arriving through the
  poll instead of through a keystroke.

  **Superseded, do not restore:** oldest-first, mirroring what `claim` would
  deliver.
- Keyboard focus is visually unambiguous: the selected list row receives a
  full-row highlight (reverse video or an equivalent colour-independent
  attribute) and retains a text marker as a fallback. Stacked, a list row IS
  the whole row, so the highlight covers it end to end — and it covers
  nothing else: never the rule below it, never a detail row. Arrow keys and
  `j`/`k` move that highlight immediately. Selection remains distinct from the
  row's pending/claimed/notice state and never implies that it has been
  consumed.
- Browse mode provides Vim-compatible navigation aliases: `j`/`k` move one
  row, `gg`/`G` jump to the first/last row, `Ctrl-U`/`Ctrl-D` page the inbox,
  and `h`/`l` choose the previous/next multipart leaf. `R` refreshes, leaving
  `g` available as the `gg` prefix. Arrow and Page keys remain available.
  These mappings never leak into reply/compose modes, where printable letters
  remain literal message text.
- **SUPERSEDED — see §16.** This said moving the cursor never creates a
  claim, and that `Enter` was the only action that took ownership. Slawomir
  reversed it for directed messages: highlighting one claims and opens it.
  The rule survives unchanged for BROADCASTS and for the poll, which is where
  most of its value was.
- Text in the detail pane is soft-wrapped to its actual display-cell width at
  whitespace; it is never silently clipped at the pane edge. A token wider
  than the entire pane is not fractured across visual rows: the current
  starting behavior shows the fitting prefix followed by U+2026 (`…`) so the
  hidden remainder is explicit. The underlying content remains intact.
  Horizontal panning of such a line may be added after trial feedback, but is
  not part of this correction round. Headers use the same explicit truncation
  rule. Reply drafts and compose fields remain lossless and must keep the
  active input tail/caret visible rather than hiding editable text behind an
  ellipsis. Explicit newlines remain paragraph boundaries, hostile control
  text is neutralized before wrapping, wide/combining characters never push a
  row past the terminal width, and detail scrolling/counting operates on the
  resulting visual lines after every resize.
- Claim state and the required next action are always visible. After a claim,
  the message remains visibly unresolved until `reply` or `close` succeeds.
- A persistent bottom status bar reports asynchronous refresh activity and the
  result of state-changing actions without stealing focus from either pane.
  Successes, warnings and errors use an explicit severity and concise text.
  An expected Baton failure or race is rendered there instead of terminating
  the console; the selected row, claim obligation and recoverable model state
  remain honest and unchanged when the underlying operation does not commit.
- `r` enters an inline reply mode. The human types a short reply and presses
  `Enter`; it is sent immediately as `text/markdown; charset=utf-8`, inherits
  the incoming subject by default, resolves the claim, and advances the
  inbox. `Esc` cancels. This path creates no temporary body file.
- `n` first opens a recipient picker populated from the validated Baton
  participant registry through the public core API. Recipients are sorted
  deterministically and each visible entry has a single-letter shortcut
  (`a`-`z`); deployments larger than one alphabet page use explicit paging
  while retaining single-key selection. Choosing an entry enters compose mode
  with a read-only selected recipient, so no free-form participant address can
  be mistyped. Picker browsing performs no authority writes, `Esc` cancels,
  and a recipient removed before send fails visibly while preserving the
  draft.
- **An EXTERNAL part is readable, not merely listed.** Its bytes live in a
  configured root, hash-pinned and verified at claim time, so the envelope
  carries a pin instead of content. Rendering it as `(no retained bytes)`
  described it as empty -- that message belongs to a SCRUBBED transient body,
  where the manifest really did outlive the payload, and `storage` is what
  tells the two apart. The header states the pinned location and size; `v`
  reads a text part into the pane through a read-only, owner-checked,
  pin-revalidating core call, bounded for display and refusing non-UTF-8 and
  non-text media. `m` cannot serve this: the core refuses to copy an external
  part into a projection because it is already a file, which is correct and
  left reading it with no key at all.
- Multipart content is navigable inside the detail pane. In browse/open mode,
  `h`/`l` select the previous/next leaf (`[`/`]` remain aliases); `Tab` stays
  reserved for compose fields and recipient-picker paging. Only the selected
  leaf's **part header line** is highlighted, never its content, so the human
  can see exactly what `m` will materialize without turning the whole body
  into a selection band. Each header identifies the manifest address,
  declared media type, disposition, and optional **part name** (carried by the
  protocol's advisory `filename` field). The TUI calls it a part name because
  it is not a filesystem name until materialization, and even then it remains
  only an input to safe output naming, never a trusted path. Safe text parts are
  readable; binary/base64 and integrity metadata are summarized and hidden by
  default. Materializing a part is an explicit core action and uses a safe
  generated output path rather than writing the advisory filename directly.
- Notices have their own visible state and never masquerade as claims. Inbox
  polling may repeatedly list UNSEEN NOTICE METADATA without recording a
  receipt, but it never returns notice content. Selecting or previewing a
  notice does NOT mark it seen. A separate explicit “mark seen and open”
  action atomically records that participant's receipt and returns the
  content, preserving the existing at-most-once crash window. Existing agent
  `see` behaviour is unchanged. New message, notice, close and attachment
  actions remain first-class operations.
- Terminal input is hostile. Text rendering must neutralize control/escape
  sequences; Markdown and HTML are never executed; advisory filenames are
  never used directly as filesystem paths.
- The initial TUI uses stdlib `curses`; it introduces no third-party runtime
  dependency. That choice can be revisited only for a concrete need and never
  changes the CLI artifact's dependency set.

### Crash/restart requirement

The current CLI can list an active claim after restart but has no targeted way
to re-read that claim's delivery. A TUI cannot safely depend on process memory
for the only readable copy. The shared core API must therefore support
re-opening an active claim owned by the participant without creating another
claim or changing its ledger history. Re-opening revalidates external parts
and fails closed if a pin changed. This is an API/tool capability, not a new
SQLite protocol unless implementation evidence proves otherwise.

Ownership is checked before ANY delivery content is returned. If an external
pin changed after claim, re-open returns safe headers plus a structured damage
report, withholds every content byte, and leaves the claim active. The TUI
must show the explicit resolution path (close/recovery followed by audited
quarantine where applicable); it never strands the user behind a generic
rendering failure or delivers the stale part.

### Core enhancements are in scope

Slawomir explicitly authorized changes to the shared core that make the human
UI correct and usable. The TUI is not required to contort itself around a CLI
surface designed only for one-at-a-time agent consumption. In-scope examples
include richer stable inbox rows, a non-claiming scan/poll/wakeup operation,
targeted active-claim re-open, and read-only notice/part metadata needed by the
two panes.

These capabilities belong in the shared public API and may also receive thin
CLI commands when independently useful. They must preserve the existing
claim, notice-receipt and audit invariants: the POLL never claims, claim
re-open never creates a second claim, listing never marks a notice seen, and
state changes still use the core's transactional operations. (This said
"observation never claims", when SELECTION was observation too; §16 moved
selection to the commit side for directed messages and left the poll and the
broadcast rules untouched.) Core growth
does not authorize TUI code or TUI dependencies in the agent CLI artifact. A
schema or protocol change remains an escalation if evidence shows one is
actually required.

## Sequencing

Next after the post-cutover cleanup review closes.

**The multipart dependency is gone.** The typed content envelope and the
convergence of attachments into parts both shipped in protocol 9, so the
console is built against the real content model rather than a placeholder to
be replaced later. That removes the part/view isolation this finding
previously called for as a hedge: there is nothing left to swap in.

The contract to build against is `README.md` ("Content: typed and
multipart-capable" and "Subject"), `AGENTS-MAILBOX-PROTO.md`, and the
`TestTypedContentEnvelope`, `TestAttachmentPartConvergence` and `TestSubject`
suites — not any prior finding document.

What the console can now rely on:

- every body is an ordered `parts` tree with a declared `content_type`,
  `disposition` and optional advisory `filename`;
- each leaf carries exactly ONE representation, named by `encoding` -- `text`
  or `base64` -- so rendering dispatches on one stable key instead of probing;
- `filename` is advisory and must NEVER be used to open, create or name a
  file, which is a console-side hazard as much as a protocol one;
- Baton itself renders nothing. A console that renders HTML or Markdown owns
  that injection surface entirely and must treat every part as hostile input.

## Acceptance criteria

- A human can wait for, inspect, reply to, and close directed messages without
  manually parsing raw JSON.
- A human can remain in an inbox/wait loop after handling a delivery instead
  of manually reconstructing the wait command each time.
- Short ACKs, status updates such as “still working; give me more time,” and
  simple decisions can be sent inline without creating temporary body files.
- The workflows previously covered by the local `wait_for_msg.sh`,
  `reply_with_claim.sh`, and `close_with_claim.sh` helpers are first-class
  console actions rather than machine-specific scripts.
- A human can inspect and publish notices and work with attachments.
- Content is rendered according to its declared `content_type`, with safe
  fallbacks for unsupported media and no execution of untrusted markup.
- Encoded binary payloads and integrity metadata are not displayed unless
  explicitly requested.
- Multipart messages are navigable: a human can see that several parts exist,
  choose among `multipart/alternative` variants, and materialize a specific
  part.
- Claim state and the next required lifecycle action are always visible.
- Every state-changing action goes through the Baton executable/API and
  preserves its transactional and audit guarantees.
- The console remains standalone and contains no host-project or
  Drift-specific assumptions.
- `baton` and `baton-tui` both use the public `baton-core` package; protocol
  and transactional logic is not duplicated.
- The CLI distribution contains no TUI implementation or dependency and does
  not grow merely because the TUI exists.
- The TUI and CLI can be versioned and released independently within an
  explicit core compatibility contract.
- A restart with an active claim can restore its readable delivery and finish
  it without a second claim or raw-authority access.
- Repeated inbox refreshes, selection changes and quick previews create zero
  claims and zero notice-seen receipts.

## Implementation plan to review with the implementer

1. Freeze the current CLI implementation as the parity oracle. Copy its Baton
   implementation into the new shared-core package; do not switch the CLI yet.
2. Define the narrow public client API on that core, including scan,
   exact-message claim, active-claim reopen, reply, close, notices, multipart
   inspection and materialization. Run old-CLI/new-core differential checks
   against fresh equivalent instances throughout the temporary duplication.
3. Add the separately built `baton-tui` against the core, with a testable
   screen/state model, the two-pane inbox/detail flow and inline reply mode.
   Prove the core and TUI before putting the agent channel on either.
4. Exercise the built artifacts against temporary instances: queue choice,
   FIFO warning, claim/reply/close lifecycle, restart with an active claim,
   notices, hostile terminal text, multipart navigation and packaging
   isolation.
5. Build `baton-core` as an importable library package with no executable UI,
   and build `baton-tui` as the separately runnable frontend that consumes
   it. Leave the existing `baton` CLI source, executable, builder and
   distribution unchanged while Slawomir uses the core+TUI combination
   against a trial instance for a human-acceptance period. Passing automated
   tests is not a substitute for this gate.
6. Adoption of `baton-core` by the existing `baton` CLI is authorized only as
   a SEPARATE next stage. First bring this protocol-9 TUI+core tree to a happy,
   reviewed commit with the CLI untouched. Then create a new work folder and
   branch for CLI adoption, remain on protocol 9, delete the frozen duplicate,
   and rerun the complete CLI, distribution, deterministic-build and
   differential-parity gates. Do not interleave that stage with this commit.

The live protocol-9 executable and authority remain untouched throughout
development. Work uses repository artifacts and temporary test instances;
the communication channel stays live. Packaging and UI structure alone do not
justify a protocol bump. Slawomir separately approved protocol 10 to replace
the misleading part `filename` concept with `part_name`, but parked it behind
two formal landed gates: first commit this protocol-9 TUI+core work with the
CLI untouched; then, in a new work folder and branch, move the CLI onto
`baton-core` without leaving protocol 9 and land that consolidation. Only then
may protocol 10 begin once in the shared core. That later work is pinned in
`work/finding-part-name-semantics/`. The live protocol-9 deployment remains
available until any eventual protocol-10 implementation and cutover are
reviewed; a fresh authority must restore communication before optional history
work.

---

# Normative UI contract (durable)

Everything below is the contract, not a discussion record. Baton traffic is
coordination; this file is the authority. An agent rebooted with no mailbox
history must be able to build the right console from this section alone --
which is also why the SUPERSEDED decisions are written down rather than
deleted, so nobody resurrects one by finding it reasonable.

Constraints that bound every item: **protocol 9 unchanged, no schema change,
and the released CLI, its artifact, its builder and its manifest byte-frozen.**
The console reaches the authority only through `baton_core`; direct SQLite
from the TUI is forbidden.

## 1. Send confirmation

Enter ARMS; it never publishes. `y`, `Y` or a second Enter publishes; `n`, `N`
or Esc returns to the unchanged draft and the same active field. Every other
key is inert -- no browse command fires and no character reaches the draft.

While armed, the footer is EXACTLY ONE ROW and that row is the whole footer:

    Send now? [Y/n]   Enter or y = send   n or Esc = keep editing

Square brackets are required. No severity prefix, no separate status row, no
`acting on` row, no duplicate in the detail pane. The row the second footer
line would have taken goes to the PANES, so the screen remains exactly as tall
as the terminal. Narrow terminals may clip from the right, but the row always
begins `Send now? [Y/n]`.

The literal must be pinned BY VALUE in the tests, not by comparing the screen
against the constant that produced it: that form of assertion let the brackets
drift and stayed green.

**Superseded, do not restore:** a two-row treatment
(`SEND THIS? …` plus `[!] Send? Y/n`); an abbreviated `Send? Y/n` with no
legend; and a rule making a second Enter inert.

## 2. Subject-only shorthand

For directed compose AND notices: when the subject is non-empty and the body
and attachment are empty, the SUBJECT TEXT becomes the single
`text/markdown; charset=utf-8` content part as well as the subject.

- Never a zero-byte placeholder part -- an empty leaf is unreadable to
  anything that renders content rather than headers.
- A body suppresses it; an attachment suppresses it (subject + attachment
  stays attachment-only, with no synthesized inline duplicate).
- Truly contentless -- no subject, no body, no attachment -- is refused, with
  no mutation and buffers preserved.
- Emptiness is tested WITHOUT `strip()`: a whitespace-only body is bytes the
  store accepts, and indentation is content in Markdown.

## 3. INBOX and SENT

ONE list pane with two views. **Not a split** -- the pane is 40% of the body
already, and halving it makes both lists unreadable. (Written when the pane
was the full-height left column; the rule survives the stacked layout
unchanged, because what it is about is one pane showing one list at a time.)

- `i` selects INBOX (default, actionable, newest-first, existing semantics).
  `o` selects SENT. One key each, and switching performs NO authority write.
- Each view keeps its OWN cursor and scroll; switching back lands where you
  were.
- SENT is newest-first by a TOTAL order, `(created_ts, id)` descending.
  Pinned as that property, NOT against `scan`'s pending order, which sorts by
  `created_ts` alone -- two messages sent in the same second come back from it
  in whatever order SQLite produces, so comparing would pass or fail on timing.
- SENT contains directed messages authored by the participant, including the
  response messages replies create, and authored notices while retained.
- Badges: `[Q]` queued, `[P]` picked up, `[R]` replied, `[C]` closed, `[E]`
  expired, `[X]` quarantined, `[N]` notice. The directed mapping is
  `messages.state` directly. The badge table must cover every state the schema
  permits, so a state the authority can produce never renders unknown.
- A notice shows RECEIPTS and EXPIRY, never a borrowed claim state: it has no
  claim, so `pending` and `claimed` would both be lies.
- Retention/GC is authoritative. A collected row disappears from the view; no
  content is duplicated into a UI-owned store.
- SENT is READ-ONLY in the strongest sense: navigating, switching and opening
  produce no claim, no receipt, no transition and no audit row.
- Enter on a sent row opens YOUR OWN copy read-only through the core.
  Owner-checked in the CORE, not merely hidden by the view, and external pins
  revalidated exactly as delivery revalidates them -- the sender is the last
  person who should be shown bytes that no longer match what the recipient
  will get.
- Core API: `list_sent`, `open_sent`, `open_sent_notice`, all read-only, no
  write lock, callable while holding a claim.
- **No default cap on history.** `list_sent` returns everything by default. A
  cap would leave older durable subjects in the authority, unreachable, while
  the view called itself history and nothing on screen said so. Retention and
  gc already bound how much exists; a second silent bound would only hide what
  they kept.
- The selection stripe follows the ACTIVE view. It read inbox state while the
  pane drew sent rows, so in SENT it landed on the wrong row -- or on none at
  all when the inbox was empty.

After a successful send the console stays in INBOX and the status bar keeps
`Sent: <subject> to <recipient> — o to view` until the next event.

## 3b. MESSAGES: unified retained activity

MESSAGES is the primary pane and holds RETAINED ACTIVITY: every message where
this participant is sender OR recipient, across the whole lifecycle. It is not
a queue of what is owed and not a received-only history.

Two failures drove this, both found by using it. Answering a message made the
original vanish -- the human answered something and watched their own evidence
disappear. Composing and sending made the new message vanish too, because
outbound lived only behind another key.

- `i` selects MESSAGES. There is NO separate History view.
- Every state appears: `pending` and `claimed` are the actionable ones,
  `completed`, `closed`, `expired` and `quarantined` carry `[R]` `[C]` `[E]`
  `[X]`. Answering CHANGES THE BADGE; the row keeps its place.
- **Direction is unambiguous.** Delegated outbound work must never be mistaken
  for inbound work owed.
- **A REPLY is an indented child of the message it answers**, marked with
  `↪` (U+21AA, ASCII `->` where the terminal cannot encode it) and indented
  two cells per level. Newest-first put a reply immediately ABOVE its own
  parent, where it reads as two unrelated messages that happen to share a
  subject -- and the row a human looks at to see whether something was
  answered is the row of the thing they answered.

  Two orders, deliberately different. THREADS sort newest-first by their most
  recent member, so answering an old message brings the conversation back to
  the top; by the root's own timestamp a reply you just sent would appear near
  the bottom, which is the "I sent it and it vanished" failure in a new hat.
  WITHIN a thread it is oldest-first under the parent, because that is the
  order the conversation happened in and a child that precedes its parent is
  not a child.

  **Indentation is bounded at THREE explicit levels** (Slawomir's ruling).
  Past it every row is still shown, in its true position, order, badge and
  direction, with `responds_to` untouched -- only the INDENT is clamped, and
  the marker becomes `…↪` (ASCII `...->`) so three levels and nine do not look
  identical. Unbounded, a long thread pushes the subject off the right of the
  pane, which loses the message to preserve the shape of the conversation.

  Presentation only: badges, direction, actionability and authority order are
  untouched. `responds_to` is followed only within the VISIBLE set -- a reply
  whose parent has been collected is a root, because indenting it under
  nothing would show a relationship that is not on screen. The indent lives in
  the SUBJECT column and nowhere else, so the badge, date and party columns
  stay aligned across every row.
- **Outbound rows carry the SENT badge in MESSAGES**, for every directed
  state including `pending` and `claimed` — `[Q]` and `[P]`, not the inbound
  notation. A blank means "waiting for me" and `*` means "claimed by me", so
  borrowing them for someone else's queue reports the wrong person's
  obligation, and whether delegated work has been picked up is exactly what
  the primary list exists to show. Inbound notation is unchanged beside it,
  and both are drawn at ONE column width so the date does not shift between
  rows.
- **One viewport authority.** How many list rows are drawn depends on whether
  the list overflows — an overflowing list spends its last row on the
  indicator, one that fits does not — and the model's scrolling, both list
  panes and the selection styling must all reach that conclusion the same
  way. Two heights for one pane hid a message at exactly-capacity, with no
  indicator to say anything was hidden. The contract is: the selected row is
  always drawn, and no row is ever off screen without the pane saying so.
- The header's awaiting-reply/close count is INBOUND OBLIGATIONS ONLY.
- Only actionable INBOUND rows may bind actions. Outbound rows open read-only
  through `open_sent`; handled inbound rows through `open_received`.
- `o` may remain as a Sent-only FILTER, but it cannot be the sole location of
  outbound history.
- Read-only in the strongest sense: navigating, switching and opening create
  no claim, receipt, transition or audit write. Switching to it disarms every
  effectful action, like switching to SENT.
- Enter reopens the original through `open_received`, owner-checked on the
  RECIPIENT in the core. That is a separate method from `open_sent` on
  purpose: one function taking "either end" would be one edit away from
  letting anyone read anything.
- No default cap, for the same reason as SENT.

**Key-map consequence, recorded because it moved an existing binding:** `h`
was leaf navigation. Leaf navigation is now `[`/`]` -- always its primary
spelling -- plus `H`/`L`. The Vim-style `h`/`l` aliases were mine; `h` for
history was specified.

## 4. Replying

**To a notice:** a NEW DIRECTED MESSAGE to the notice's author. Never a claim
on the notice; `messages.responds_to` references a message, so pretending
otherwise would mean lying to the schema. Seen semantics are exactly what the
explicit open already set. The author is taken from the notice with NO picker.

**To a directed message:** a disposition that resolves the claim, through the
core's existing linkage. (Settled; see §8.2.)

In both cases the ORIGINAL stays visible -- headers and body -- while the
reply is written and through the confirmation. Declining restores the draft
AND the context. The authority's original content is immutable and is never
what the console writes to.

## 5. Body editing: external only

**There is NO inline body text editor.** Printable text never accumulates in
an inline body buffer. Any action to write or edit a body opens the configured
external editor immediately. This removes the merge question entirely.

- `r` on an opened directed message or notice starts a QUICK REPLY SUBJECT
  editor, addressed automatically to the original author, caret in the
  subject. Enter then the confirmation sends it through the subject-only
  shorthand, using the resulting subject text as the single Markdown part.
- A full/body reply opens the external editor directly. `e` is the browse
  action (verified unbound).
- New compose and new notice start in the SUBJECT, for the quick path. Ctrl-E
  from compose opens the editor on the current external body draft.
- Reopening the editor always opens exactly the last imported body draft. It
  never re-seeds and never loses edits.
- Attachment entry stays a separate compose field. Subject + attachment with
  no body remains attachment-only; a body added through the editor coexists.

**Superseded, do not restore:** the hybrid model where a body was typed
inline and Ctrl-E optionally took it to an editor. It has no defensible merge
rule.

## 6. The external editor

Selection precedence: `--editor`, `BATON_EDITOR`, `VISUAL`, `EDITOR`, then
`vim`. TUI-only -- a UI preference in the authority config is one every agent
carries and none can use.

- Parsed with `shlex` and run as ARGV. **Never a shell.** A configured editor
  may have arguments; it may not have a pipeline, a redirect, a substitution
  or a second command.
- `--` is appended only for editors known to treat it as end-of-options.
  Otherwise the validated temp path is simply the last argv item, always
  exactly one.
- Our default invocation disables modelines (`vim -n --cmd 'set nomodeline'`):
  a modeline is a line INSIDE the text that configures the editor, and the
  text arrived from another participant. A user-supplied invocation is left
  exactly as configured -- that is their trust boundary.
- The draft is a private 0600 regular temp file, verified on return to be the
  SAME file by device and inode, size-bounded, and removed whether the edit
  succeeded or failed. A symlink or replaced inode is refused, not imported.
- No authority or storage path is ever passed to an editor.
- Curses is suspended cleanly, the editor runs on the real terminal, and the
  screen is re-measured and repainted on return.
- **Importing is not publishing.** Save-and-quit is muscle memory; sending to
  another person is a decision. The ordinary Enter and `Send now? [Y/n]` still
  stand. Missing editor, nonzero exit, signal, unreadable or replaced file all
  leave the draft exactly as it was -- a half-imported body is worse than no
  import.
- An empty reply draft seeds an EDITABLE quote: `On <date>, <author> wrote:`
  with every line prefixed `> ` and room above it. Binary parts are never
  quoted in. The copy is the author's to cut down; the original is immutable.
- Round-tripping is byte-exact: whitespace, tabs, newlines, an absent final
  newline and non-ASCII all survive.
- The draft is opened ONCE and everything is decided about that descriptor:
  `fstat` it, compare device, inode, type and size, read from it, with
  `O_NOFOLLOW` where available. Checking a PATH and then opening it is two
  lookups of the same name at two instants, and the name can be replaced in
  between -- the check passes on our file and the read gets the attacker's.
- **An empty body from an explicitly opened editor REFUSES.** The quick path
  is valid, but someone who chose the full-body path and got an empty body
  back must not have the subject line sent in its place: that is a different
  message from the one they set out to write.

## 10. The console never rewrites what the human typed

The core rejects a subject with leading or trailing whitespace deliberately,
because silent sanitization misrepresents what the sender wrote. The console
therefore passes the draft EXACTLY and surfaces the refusal, keeping the
draft. It must never `strip()` on the way past: that hides a refusal the human
is entitled to see AND sends something they did not type.

Empty means omitted, which is intentional and different: there is nothing to
misrepresent.

## 7. Required regressions

Confirmation literal and one-row structure; shorthand and its suppressors;
contentless refusal; whitespace validity; SENT badges with full schema
coverage, ordering, per-view selection, zero-write observation, owner-only
open, stale-pin fail-closed, restart persistence, retention disappearance;
notice reply creating one directed message and no claim, with receipts
unchanged by beginning or cancelling; editor precedence, argv/no-shell, temp
file privacy and cleanup, success/nonzero/missing/signal/unreadable, no
publish on exit, byte-exact round trip, existing draft never re-seeded, binary
not injected, modelines disabled; original authority bytes unchanged; frozen
CLI and packaging hashes.

Every fix must be verified by REMOVING it and watching its pin fail. Three
faults this round were found that way and would otherwise have shipped green.

## 8. Decisions, both settled

1. **Reply subject — RULED, closed.** The original subject is copied
   EXACTLY, for directed replies and notice-to-author replies alike. No `Re:`
   is ever added.

   Slawomir's rationale, recorded because it is the reason and not just the
   outcome: `[R]` in SENT already exposes replied state, and
   `responds_to`/`thread_id` carry the actual relationship. A prefix would be
   decorative redundancy, and subject churn in a long thread where the same
   words drift by one prefix per hop. Quick-reply mode still lets a human
   edit or replace the copied line deliberately, which is the difference that
   matters.

   **Superseded, do not restore:** seeding `Re: ` exactly once,
   case-insensitively non-stacking. It was implemented and pinned first, on
   the standing instruction at the time; its test now records what it used to
   assert, and the semantic property it existed for -- a thread's subject does
   not accumulate noise -- is unchanged and now absolute.

2. **Reply act — RULED, closed.** Directed `r` (quick) and directed `e`
   (full) both remain claim-completing DISPOSITIONS through `store.reply`.
   Their subject and body UI must never turn them into ordinary sends or
   leave the claim active. A notice `r`/`e` is a new directed send, because a
   notice has no claim to complete.

   Pinned, for both paths and both kinds:
   - directed: dispositions +1, messages +1, claims unchanged, the claim's own
     `state` reaching `completed`, and `unresolved_count() == 0`;
   - notice: messages +1 with dispositions, claims and notices all unmoved;
   - which act fires is decided by what is OPEN, never by the cursor -- pinned
     with a notice and a directed message both in the list.

   Verified by breaking it: making the directed reply an ordinary send leaves
   dispositions at zero and the claim active, and routing a notice reply
   through the claim path fails the notice pins.

## 16. Claim-and-open on highlight — RULED, a major supersession

**Highlighting an inbound directed row claims it and shows its body.**
Scrolling to a row and then pressing `Enter` was judged one ceremony too many
for a human console, and Slawomir accepted the ownership tradeoff explicitly.

This changes WHEN the TUI invokes the existing exact-message claim/open
operation. It changes nothing in the core, the CLI or the protocol.

- Applies to the startup selection, `j`/`k` and arrows, paging, and `gg`/`G`.
  A page or jump claims only the row actually LANDED ON, never the ones
  skipped.
- pending → claim that exact message and show its content; already claimed by
  this participant → reopen without a second claim; handled or outbound →
  open the retained copy read-only and arm a follow-up, as before.
- **The accepted consequence, stated rather than discovered:** moving across
  several pending rows leaves several unresolved claims. None is ever
  auto-closed or auto-replied. The unresolved count, the badges and the quit
  confirmation are what protect them.

**What did NOT change, and is what keeps the tradeoff bounded:**

- **Polling never commits.** An arrival is not claimed because it arrived, and
  restoring the same selection does not re-claim.
- **Selection resolves by IDENTITY.** A reordering poll can never let a
  numeric cursor claim a different message — the wrong-target bug's
  consequence is now a claim rather than a misdirected keystroke.
- **Notices stay explicit.** Highlighting an unseen broadcast records no
  receipt; `Enter` remains the atomic mark-seen-and-return. Claim-on-highlight
  was authorised for directed messages, not for implicit consumption of
  broadcasts.
- **DETAIL-focused navigation is pure UI**, because it does not move the
  selection.
- A failed or raced claim fails closed: the intended row stays selected, the
  error is shown, and no other row's content is displayed.
- `Enter` stops being advertised once the highlighted row is open — it would
  be a no-op — but remains advertised on an unseen notice.
- FIFO guidance stays informational: selecting a later message from the same
  sender still warns, and never redirects the claim to the earlier row.

**Superseded, do not restore:** the OBSERVE/COMMIT navigation split in
"Pinned TUI interaction", under which selection was always observational.

## 15. Pane focus and the context-sensitive legend — RULED

`Tab` toggles navigation focus between the LIST and the DETAIL pane;
Shift-Tab is the same toggle, not a third stop. Default is the LIST.

- **Focus is PURE UI STATE.** No claim, receipt, disposition, publication,
  transition, core read or filesystem write, and it preserves the selected
  row, action target, both offsets, selected part, draft and status. It is
  NOT an action target: the selected/opened item remains the target model.
- `i`/`o` return focus to the list, because the human just said which list
  they are navigating.
- Polling, redraw, resize and `Ctrl-R` preserve it.
- **Navigation routes through focus.** LIST: `j`/`k` and arrows move the row,
  `^U`/`^D` and PgUp/PgDn page, `gg`/`G` jump to first/last. DETAIL: the same
  keys scroll one line, a visible page, and to top/bottom. Detail navigation
  never moves the list cursor.
- Only the NAMED navigation keys route through focus. Enter, `r`, `R`, `c`,
  `v`, `m` keep their semantics.
- **`h`/`l` and the left/right arrows scroll the DETAIL pane sideways** under
  DETAIL focus, one display cell at a time, and are unbound under LIST focus.
  Part navigation is `[` and `]` ONLY.

  **Superseded, do not restore:** `h`/`l` and `H`/`L` as part navigation, and
  the earlier sentence in this section saying `h`/`l` and `[`/`]` were not
  broadened. The reason is the one that makes it a contradiction rather than a
  preference: once DETAIL focus exists, Vim `h`/`l` not moving within the
  focused pane is a visible inconsistency in the model.

  Horizontal movement is pure observation — no core call, claim, receipt,
  publication, disposition, transition or filesystem write. It exists for
  content that cannot usefully wrap; ordinary prose still wraps at whitespace.
  Nothing is destructively discarded: hidden content is indicated with the
  ellipsis convention on whichever side is hidden, never splitting a wide cell
  or exceeding the terminal width, and applied to overflowing CONTENT lines
  rather than to the structural chrome. The offset is clamped from the
  rendered detail at the current width, survives focus toggles, vertical
  scrolling, redraw, poll, `Ctrl-R` and resize, and resets when the message,
  the view or the selected part changes — because it belongs to the content
  being read. Availability comes from the same affordance authority: advertised
  and accepted only under DETAIL focus with actual overflow.
- **Superseded, do not restore:** uppercase `J`/`K` as detail scroll. Removed
  from dispatch, footer and help, with no hidden alias; pinned unbound.
- The focused pane is marked `> ` on its label — `> MESSAGES`/`> SENT` and
  `> DETAIL` — with the inactive form the same label without it. Both labels
  are always drawn and exactly one is marked. ASCII and width-stable, so
  toggling moves nothing; styling may emphasize additionally but must never
  be the only indication. **Superseded:** the R7 edge-to-edge rule, which now
  carries the `DETAIL` label so focus is visible.

**The footer is an affordance list, not a catalogue.** It advertises only
actions that are presently legal for the selected/opened object, view, focus
and mode. `c close` appears only while a claim is held that close can consume
— never for a notice, an outbound row, a handled row, the Sent view, or an
empty selection. `r`/`R`, `h`/`l`, `v`, `m` and Enter follow the same rule;
globals stay. Navigation wording follows the focus.

**There is ONE affordance query** and both the footer and key dispatch read
it, so "advertised" and "dispatchable" are one fact rather than two opinions
that drift. A refusal explains itself from the same conditions.

Three consequences of that, each found by review after the first pass:

- **`open` follows the ACTIVE VIEW**, not the message list. Reading the
  MESSAGES selection hid Enter from a selectable Sent row whenever MESSAGES
  happened to be empty.
- **Every spelling of an act answers to its affordance.** `R` is the same
  semantic reply as `r`, so it is gated by the same predicate; leaving it out
  let it stay dispatchable while the footer hid both forms, refusing through a
  second predicate inside `begin_reply`.
- **Each non-browse mode has its OWN legend**, from the same table that
  decides that mode's keys. The browse footer was drawn in every mode, so the
  help screen advertised `n new` and `^R refresh`, and the recipient picker
  advertised open/reply/close belonging to the row hidden behind it. The
  status bar stays separate, and the two confirmation footers keep their exact
  one-line form.
**Superseded:** the fixed footer literal, which is why an opened notice
advertised `c close` from the day the footer was written.

## 14. Retained notices — RULED

A notice this participant has SEEN stays in MESSAGES as history. It used to
leave the list the instant it was opened, so a human watched an announcement
disappear while they were reading it.

- `list_notices` is UNCHANGED and stays unseen-only, for its existing
  at-most-once consumers. MESSAGES uses an additive read-only
  `list_notice_activity`: every unexpired notice, LEFT JOINed to this
  participant's receipt, metadata only, no write lock.
- `seen_ts is None` → state `unseen`, otherwise `seen`.
- **`!` is unseen; `[✓]` is a retained seen notice**, with `[S]` as the
  fallback where the terminal cannot encode the check mark. `S` is defined as
  *seen* in the legend and in `?` help. **Superseded, do not restore:** `[N]`
  for a seen row -- `N` reads as *new*, which is the opposite state -- and a
  primary `[S]`. The fallback is one decision covering every optional glyph,
  and changes presentation only: both spellings are three display cells.
- Enter on an unseen notice still commits the receipt exactly once and returns
  the body atomically. Enter on a SEEN row is not a content path: no write, no
  second receipt, and the screen SAYS the content is not redelivered. The
  absence of a write is not enough on its own -- a row that looks one
  keystroke away from the announcement is a row that will be pressed.
- A body read earlier IN THIS SESSION stays on screen: it is already in
  memory, and blanking it because the poll ran would take away something the
  human is reading. After a restart the metadata is there and the body is not,
  which is what at-most-once means.
- Seen state is PER PARTICIPANT; TTL, `expire` and gc remain the only reasons
  a history row leaves the list; `r`/`R` still start a directed response to
  the author from the retained metadata alone.

## 13. Follow-ups — RULED

**An answered conversation is never presented as a dead end.** `[R]` stays on
a handled inbound row, the body stays immutable, and `c` and every disposition
path stay unavailable — the claim is resolved and a second disposition is not
a thing. What changed is that the screen stops saying "read only" and starts
saying what can still be done:

    Answered   r quick follow-up   R full follow-up      (handled inbound)
    Sent       r quick follow-up   R full follow-up      (outbound directed)

- `r`/`R` create a FRESH directed message, linked by `responds_to` to the
  SELECTED message, never a second disposition. The recipient is the other
  party — the author for inbound, the recipient for outbound — taken from the
  row rather than a picker, because "follow up on this" answers who.
- Subject is inherited under the existing quick/full rules.
- `kind` is `follow_up`: an existing field, no new schema record type or
  state. It is DESCRIPTIVE and is never the safety authority — claim and
  disposition records are, and list threading derives from `responds_to`.
- `thread_id` is inherited when the selected message has one, and never
  invented when it does not.
- Following up on the same parent creates SIBLINGS; following up on a child
  nests one level deeper, subject to the three-level visual cap.
- Pending inbound first-reply behaviour and claim authority are unchanged.

**The relation is "in reference to", not "in reply to".** The wire field stays
`responds_to` and no rename is triggered; the human-facing label is `In
reference to:` because the relation is broader than the one claim-resolving
reply. The initial reply both resolves its claim and creates the link; later
follow-ups create only a fresh linked message with their own lifecycle, and
the original's `[R]` does not move.

## 12. The modal shortcut list — RULED

`?` from BROWSE opens a modal help screen: the complete current shortcut map,
grouped by browse/list, reading and parts, reply and compose, typing, and
lifecycle actions. `?`, `q` or Esc closes it, and `q` there does NOT quit --
it is the key people press to dismiss a full-screen thing.

- **Observation in the strongest sense.** No claim, no receipt, no refresh, no
  publication, no disposition, and no lost draft. Closing restores the exact
  selection, list scroll, detail scroll, selected part, opened claim, draft and
  status; the help's own scroll is the only state it owns.
- **In every typing mode `?` is ordinary text.** A key that opened a
  full-screen view mid-sentence would be the browse table leaking into the
  text one.
- **It pages rather than clipping.** A shortcut a small terminal could not
  draw is a shortcut that does not exist -- the fault the recipient picker
  taught, in a different view.
- **The ordinary one-line status bar stays.** Help is a screen, not
  status-bar prose, and the bar is where asynchronous events land.
- **The content is generated from the key table**, so the two cannot drift. A
  help screen maintained separately is wrong within a month, and wrong help is
  worse than none because it is believed. Pinned: every live browse binding
  appears.

## 9. Key map

    r        quick reply: edits a copy of the ORIGINAL subject, unchanged
             and unprefixed, which becomes the content part through the
             subject-only shorthand
    R        full reply: starts the reply AND opens the editor, one action
    Ctrl-R   manual refresh; the two-second poll is unchanged
    Ctrl-U   in a typing mode: kill from the caret back to the start of the
             line; in BROWSE it still pages the list
    Ctrl-E   body editor from within a typing mode

Shifted `r` for the bigger version of the same act, which is the pairing
people already expect. Manual refresh moved to Ctrl-R because `R` was taken,
and it cannot go back to `g`, which is the `gg` prefix.

Inside the quick-reply subject editor every browse letter is ordinary text --
the text modes are a separate key table -- so no special case is needed.

**Superseded, do not restore:** browse `e` as the full reply, and plain `R` as
manual refresh. `e` is REMOVED rather than kept as an alias: a second spelling
nobody is told about is a key only its author can press.

## 11. Dismissing a history row — PARKED, needs protocol 10

Slawomir wants `x` on a history row to remove it from HIS view, permanently
and across launches. It is a per-participant DISMISSAL: never a deletion,
never a rewrite of the message, the disposition or the audit record.

**There is no protocol-9 mechanism for it, and none should be invented.** The
tables are `accepted_roots`, `ceremonies`, `claims`, `contents`,
`dispositions`, `instance_meta`, `messages`, `moves`, `notice_seen`,
`notices`, `op_context`, `parts`, `quarantines`, `recoveries`, `transitions`.

- `notice_seen` is the only per-participant table, and it is a RECEIPT for
  broadcasts. Writing a UI preference into it would corrupt the delivery count
  a sender reads.
- `transitions` is an append-only audit of protocol acts, with `entity`
  constrained to `message`/`claim` and `to_state NOT NULL`. A dismissal is not
  a state change, and faking one would put a lie in the audit trail.
- Nothing else is keyed by participant at all.

**RULED:** the protocol-authority row, in protocol 10, after CLI-to-core
adoption. Not a TUI-owned preference store -- a file beside the console is a
second store of truth about the mailbox: not atomic with the authority,
drifting when two consoles run, invisible to `doctor`, and the first question
after any confusing state becomes which of the two is right.

Nothing for `x` is implemented in this stage. The contract is carried in
`work/finding-protocol-10-umbrella/FINDING.md`.