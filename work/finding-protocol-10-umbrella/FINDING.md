# Protocol 10: one deliberate migration boundary

Slawomir's direction: protocol 10 is the SINGLE boundary for all known
breaking work. Inventory and resolve these together, so cutover is not
immediately followed by needing protocol 11.

**Nothing here belongs in the current TUI/core commit.**

## The bundle

Each contract stays independently reviewable inside this umbrella; the bundle
exists so the BUMP happens once, not so the review does.

| Contract | Where it is specified |
|---|---|
| CLI adoption of `baton_core` | `work/finding-human-console/PLAN.md`, stage 2 |
| `filename` -> `part_name` | `work/finding-part-name-semantics/FINDING.md` |
| General multipart / references authoring in the CLI | `work/finding-mailbox-conventions/FINDING.md` |
| Append-only claim progress, `working`/`blocked`, timestamps | `work/finding-claim-progress/FINDING.md` |
| Message priority, queue order and fairness | same |
| Durable per-participant dismissal (`x`) | `work/finding-human-console/FINDING.md` §11 |
| Scoped/team and multi-recipient audiences | `work/finding-scoped-audiences/FINDING.md` |
| Two-second dwell before TUI claim-on-highlight | this file, below |
| Presence leases, targeted blocker events, participant-pane filtering | this file, below |

## Sequencing — AGREED, and this is the order

Proposed by the implementer, agreed by the reviewer with two separations and
two corrections. Landed commit `870799a` is step 0.

### Stage 1A — the CLI adopts `baton_core`, still protocol 9

Pure adoption and nothing else. `bin/baton` changes its artifact bytes; its
behaviour and the protocol do not. `baton_v6.py` stays FROZEN as the
differential oracle — it is the instrument parity is measured with, so editing
it destroys the measurement. Acceptance is the existing corpus, differential
parity against that oracle, a deterministic package rebuild, and an explicit
artifact/hash handoff. No fresh authority, no cutover.

### Stage 1B — CLI multipart/references authoring, still protocol 9

Only after 1A is independently reviewed. The stored multipart tree already
exists in protocol 9, so AUTHORING it is CLI surface rather than a wire
change — which is the reviewer's correction to my sorting, and it is right.
Kept separate so 1A stays reviewable as pure adoption instead of mixing
migration with new behaviour.

### Stage 2 — one protocol-10 bump, one cutover

Each item written against the shape the previous one leaves:

1. `filename` -> `part_name`. Pure rename, first, so every later contract
   touching parts is written in the new vocabulary rather than translated.
2. Scoped/team and multi-recipient audiences. This changes what a RECIPIENT
   is, and the items below all reference recipients.
3. Participant-authorized read/materialize, and reread authority. AFTER
   audiences, because audiences define who is a party — the reviewer's
   correction to my proposal, which had put this in stage 1. The audit answer
   belongs here too if it needs schema: an unrecorded privileged read must not
   be the final contract.
4. Append-only claim progress AND targeted blockers — same implementation
   stage, DISTINCT contracts. Progress is claim-bound. A blocker is a directed
   participant relationship, can exist without a claim, is viewer-relative,
   and is never a blocked claim phase. I had proposed folding them into one;
   the separation is the reviewer's and is the sharper reading.
5. Priority, queue ordering, fairness.
6. Durable per-participant dismissal.
7. Presence leases last.

Presence going last is accepted. It is NOT the protocol's first expiry
concept, and describing it that way was my error: notices already carry
TTL/expiry semantics.

### Stage 3 — TUI, after the bump, no wire change

1. Re-reading, backed by the participant-authorized authority read from stage
   2.3. The console must NOT keep a second source of truth for durable
   authority content — which is the reviewer's constraint on my "keep what it
   was delivered" sketch, and it is the right one.
2. The two-second claim-on-highlight dwell.
3. The participant pane, presence display, and read-only conversation filter.

Stage 1A before everything is not preference: `filename` lives in SCHEMA TEXT
that exists in two copies until adoption lands. Renaming earlier means writing
a breaking change twice, or editing the frozen oracle.

## Why one boundary

Every bump costs a fresh authority and a cutover. Two bumps in quick
succession cost two, and the second one arrives just as everyone has finished
absorbing the first. The inventory above is the list of things we already know
we want; discovering an eighth after cutover is the failure this exists to
prevent, so the inventory is worth finishing before the bump rather than after.

## Dismissal (`x`), ruled

The protocol-authority row, NOT a TUI-owned preference store. A per-participant
dismissal table keyed `(participant, message_id)`: atomic with every other
write, durable by construction, visible to `doctor`, auditable.

The alternative was rejected explicitly: a file beside the console is a SECOND
STORE OF TRUTH about the mailbox. It cannot be atomic with the authority, it
drifts when two consoles run, it is invisible to `doctor`, and the first
question after any confusing state becomes which of the two is right.

Dismissal hides a HANDLED row from one participant's view. It never deletes or
rewrites a message, a disposition or an audit record, and it must never hide a
pending or claimed obligation.

## Claim-on-highlight dwell, ruled for the after-commit batch

Claim-on-highlight remains the TUI model, but selection must dwell for two
continuous seconds before it commits. The delay lets a human scroll quickly
past messages they intend to ignore without accumulating claims; pausing on a
pending directed message still claims and opens it automatically.

This is scheduled with the protocol-10 work even if implementation proves to
be TUI-only and requires no wire or schema change. It must not be folded into
the current protocol-9 TUI/core commit.

- Highlight and metadata preview update immediately.
- A pending inbound directed row is claimed and opened only after the same
  message identity remains selected continuously for two seconds.
- Rows passed over during rapid scrolling are never claimed. Only the final
  settled row may commit.
- Any actual selection-identity change cancels the old deadline and starts a
  fresh dwell. Leaving and later returning to a row does not reuse elapsed
  time.
- The deadline uses a monotonic clock, never wall-clock timestamps.
- Startup uses the same dwell instead of claiming synchronously, giving the
  human two seconds to move away.
- Polling remains observational: it never claims, sees, or opens an arrival.
  Reordering preserves selection and any applicable dwell by message identity,
  never by numeric row index, and can never redirect the eventual claim.
- An unseen notice remains explicit and is never automatically marked seen.
- Handled, outbound, and sent rows remain non-authority read/follow-up paths.
- A claim race at the deadline remains exact-message and fail-closed.

Required regressions: no claim immediately before the deadline; the exact
claim at or after it; rapid multi-row scrolling; final-row-only settlement;
leave/return reset; startup escape; arrival and poll purity; reorder identity;
notice non-consumption; view/selection cancellation; and lost-race failure
without displaying another row's content.

## Participant pane, presence, and blockers

This is approved for the protocol-10/TUI batch, not the current protocol-9
commit.

The console may show a narrow participant pane backed by expiring presence
leases. Presence says only whether a participant has a current `wait` or TUI
session. Use honest terms such as active/listening and offline/stale. There is
no `busy` or do-not-disturb state: Baton participants remain addressable and
serve their queues as quickly as possible.

`blocked` is NOT presence and is NOT inferred from unanswered messages. Most
messages require an answer, and a participant with ten runnable findings is
not blocked merely because questions about findings eight through ten are
pending. Silence and an expired lease mean only offline/stale.

A blocker is an explicit, append-only, directed event in the SQLite authority:

- it names the blocked participant and the participant/audience able to
  unblock them;
- it carries a timestamp, a concrete reason/action needed, and references to
  the relevant message, thread, claim, or repository paths;
- ordinary message traffic does not create it;
- it remains open until the blocked participant explicitly resumes/cancels it;
  a remote party cannot declare someone else unblocked;
- it may be atomic with a linked high-priority directed message, but it is not
  a globally broadcast status.

Visibility is viewer-relative. If `baton.implementer` is blocked on
`human.slawomir`, Slawomir sees `baton.implementer — waiting on you`, the
implementer sees `blocked on human.slawomir`, and unrelated participants see
ordinary presence. An unresolved blocker sorts its linked message above
normal work for the responsible recipient.

Highlighting a participant is a read-only automatic filter. The MESSAGES list
immediately shows the directed traffic between the viewer and that participant
in both directions, newest first; an `All` participant row removes the filter.
Changing this highlight never claims a message, records a receipt, or marks a
notice seen. The two-second message-claim dwell begins only when the MESSAGES
pane itself has focus. Enter on a focused participant begins a compose already
addressed to that participant. On narrow terminals the participant pane may be
a toggleable overlay rather than shrinking message content beyond usefulness.

Required regressions: lease renewal and expiry; crash-to-stale without a false
blocked state; blocker endpoint-only visibility; ordinary unanswered messages
never implying blocked; explicit resume/cancel; linked priority ordering;
read-only member filtering; both-direction conversation projection; `All`
reset; no claim/receipt while member focus moves; and compose addressing from
the selected participant.

## Re-reading what you have already seen, ruled for post-commit

Slawomir's ruling:

> in post-commit phase, I don't like that a seen message cannot be seen again.
> That's not good since often times we (humans) need to read again including
> our own messages or announcements that we sent out. UI should not limit to
> one-read

He is right, and the distinction that makes it cheap is already written down
in `work/finding-cli-read-authority/FINDING.md`: **re-reading is not
re-delivery.**

At-most-once is a property of the RECEIPT. A notice is delivered once, the
receipt is recorded, and no second delivery happens — that is deliberate and
is not what this touches. What the human is asking for is to look again at
bytes their own participant already received, and at their own outbound
traffic, which they authored.

So this is a console and CLI question:

- the console should keep what it was delivered, so an opened notice can be
  reopened without asking the authority for anything;
- a participant should be able to read back a message they SENT, which today
  is served only by the unscoped `materialize`;
- `see` reporting nothing for a notice whose receipt exists is honest about
  delivery and unhelpful as an interface; it should distinguish "not
  redelivered" from "not available".

None of that weakens at-most-once, and none of it needs a wire change. What it
does need is a decision about where the local copy lives and who may read it
back, which is why it sits here rather than being done quietly.

Recorded when it was ruled; not started. It is a post-commit item by
Slawomir's own words.

## Vi Normal/Insert modes

**This is not a confirmed direction. It is exploratory, and it needs more
research and discussion before anyone treats it as work.**

It is kept as a finding because the question is worth having on the record;
that is not the same as being scheduled. Nothing in the bundle above depends
on it and it carries no acceptance criteria.

Loose discussion, recorded so the idea is not lost, and explicitly NOT a
decision:

> restrained TUI Normal/Insert modes; `?` works in Normal; no protocol change

**Nothing here is approved or pinned, and `Esc` remains CANCEL** unless a
later ruling changes it. An earlier version of this section described the
"Esc preserves draft" clause as settled; it is not, and the correction that
said so is why this paragraph exists in this shape.

Both the original message and its correction arrived with ZERO-BYTE bodies, so
everything above comes from subject lines. That is the whole record, which is
exactly the reason not to design from it: a subject is a summary someone wrote
for a list, not a specification.

Slawomir is NOT sold on reassigning `Esc`, and it stays cancel. If this is
ever taken up it needs an actual statement of intent first — this section is
not one, and must not be read as scoping anything.
