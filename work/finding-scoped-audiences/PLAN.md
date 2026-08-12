# Stage 2.2 — scoped audiences and multi-recipient delivery

Two features in one finding, and they do not share lifecycle semantics. A
scoped notice is still a notice: broadcast, at-most-once, never claimed. A
multi-recipient directed message is still claimable work, once per recipient.
Building them as one mechanism would be the mistake the finding warns about in
its second paragraph.

Written before code. The global-notice decision below was ruled by Slawomir on
2026-08-10: global notices freeze the configured recipient set at publication.
The publication-retry decision was also ruled on 2026-08-10: protocol 10 stays
at-least-once and uses a sender-supplied possible-duplicate warning, not a
publication token.

## Scoped notices — the easy half

`notices` gains nothing. A new table records the frozen audience:

    notice_audience(notice_id, participant)   PRIMARY KEY (notice_id, participant)

The selector expands against the participant registry inside the publishing
transaction, and the expansion is what is stored. `notice_seen` already keys on
`(notice_id, participant)`, so independent at-most-once receipts come for free.

Delivery becomes "notices whose audience contains me" instead of "all
notices". A global notice stores every configured participant at publication,
which makes global and scoped the SAME mechanism rather than a special case —
and makes "frozen at publication" true for global notices too, which today it
is not.

That last point is a behaviour change worth naming: today a participant added
after a global notice was published can still see it. Under this model they
cannot. Slawomir confirmed this reading on 2026-08-10: global and scoped notice
audiences both freeze at publication.

The selector grammar is `<segment>(.<segment>)*.\*`, matching complete dotted
segments only. `baton.*` matches `baton.reviewer`, never `baton_extra.reviewer`
— which falls out of splitting on `.` rather than of string prefixes, and the
test for it is `baton_extra.reviewer`.

An empty expansion is refused: a notice addressed to nobody is a publication
that silently does nothing.

## Multi-recipient directed messages — the decision

The finding permits shared content storage "only if retention, damage, audit,
GC, and disposition invariants remain independent and exact". That is the
whole design question, and there are two shapes:

**A. N messages, one content.** Each recipient gets an ordinary row in
`messages`, sharing `manifest_sha256` and the stored parts, linked by a new
`publication_id`. Every existing invariant — claim, retry, disposition,
damage, quarantine, recovery, retention, GC, doctor — applies unchanged,
because these ARE ordinary messages. The audience is recorded for display and
audit.

**B. One publication, N deliveries.** Normalized: a `publications` row holds
content and subject, `deliveries` rows hold per-recipient state. Fewer
duplicate columns, and every one of those invariants has to be re-derived
against a shape it has never seen.

**A is ruled**, and the reason is not effort. The finding's requirement is
that per-recipient lifecycles stay independent and exact. Under A that is true
BY CONSTRUCTION — there is nothing to keep independent, because they were
never joined. Under B it is true only for as long as every future change
remembers to keep it true, and the failure mode is one recipient's close
resolving another's delivery.

The cost of A is honest and bounded: duplicated envelope columns plus an
immutable `publication_id` link to the canonical audience.

**AND A PUBLICATION RECORD IS STILL REQUIRED.** "N ordinary messages" is the
LIFECYCLE shape; it is not permission to derive the audience from whichever
message rows survive. GC or transient retention can remove one recipient's
terminal delivery while another has not opened theirs, and an audience derived
from survivors would silently shrink — changing the detail header and the
authorization state that later features read.

So:

    publications(publication_id, from_participant, kind, subject, thread_id,
                 retention, outcome, container_type, manifest_sha256,
                 audience_kind, selector, created_ts)
    publication_audience(publication_id, participant)

Identity and audience ONLY. No delivery state: claims and dispositions stay on
the ordinary messages, which is the whole point of shape A. Every directed
message carries `publication_id`, including single-recipient ones — later
decision obligations and participant-authorized reread need one
publication-time audience model, not a private-message special case.
Response messages created by `reply` also receive their own single-recipient
publication record; the claim disposition remains their effectively-once
operation key.

Triggers and `doctor` must prove: publication and audience are immutable and
non-empty; exactly one delivery per audience member; every linked delivery
agrees on sender, subject, kind, thread, retention, outcome, container type
and manifest; no delivery outside the canonical audience; and GC of one
delivery cannot remove audience metadata another still needs.

Parts are already keyed by `owner_kind`/`owner_id`, so under A each message
owns its own part rows pointing at shared `contents` — which is how a single
recipient's quarantine can damage one delivery without touching another's.
That is the property B would have to invent.

## Publication retry — ruled at-least-once with a warning

The plan said retry identity "is extended to include audience kind, the
selector, and the canonical recipient set". That describes a comparison that
has nothing to compare against.

`send` and `send_notice` GENERATE a new id every time and are not
retry-addressable at all. There is no way for a caller whose result was lost
to name the publication it may already have made. So "a retry that would
address a different set fails closed" was a promise with no mechanism behind
it, and I should not have written it as though the audience were the only
missing piece.

Before the ruling, effectively-once publication would have required all of:

- a caller-known publication token, and how the CLI and the TUI generate,
  retain and resend it;
- exact redelivery of the prior result after a post-commit, pre-result crash;
- mismatch checks over manifest, sender, subject, kind, thread, retention,
  outcome, audience kind, selector and canonical audience;
- retention and GC of the retry record, including whether a token may ever
  become reusable — preferably never within retained history;
- NOT a content hash as the token: two deliberate identical publications must
  remain possible.

Slawomir ruled on 2026-08-10 that protocol 10 keeps publication at-least-once.
There is no caller-known token and no exact retry redelivery in this stage.
The finding's earlier audience-retry promise is withdrawn rather than left
quietly unmet.

An ambiguous retry is a new publication. The sender can mark it with an
immutable `possible_duplicate` warning, delivered to every recipient and
shown in history/inspection surfaces. The flag is advisory: without a token
Baton cannot identify the original and must not claim that it proved a
duplicate. Two deliberate identical publications remain ordinary unmarked
publications.

The flag is accepted by the at-least-once `send` and `send_notice` publication
paths. For directed sends it is stored once on `publications`; for notices it
is stored immutably on `notices`. It is not a substitute for the existing
claim-ID retry contract on `reply` or `close`, which remains unchanged.

Duplicate recipients are refused at publication rather than deduplicated
silently, per the finding — deduplicating would make `--to a --to a` mean
something the caller did not write. That part stands regardless.

## Config regeneration

`regen_instance` already refuses to remove a participant named by a live
message or notice. The gate extends to stored publication and notice
audiences while they remain deliverable or actionable — otherwise a removal
can freeze a participant into an audience and simultaneously make them unable
to consume it.

Config ADDITIONS never join an existing audience; membership comes only from
the stored expansion. Removal becomes possible again when the audience is
terminal or collected, without ever rewriting retained history.

## Wire and API shapes, to be settled before code

- single-recipient `Store.send`: return shape unchanged, plus
  `publication_id`;
- multi-recipient: `publication_id` and the recipient-to-message mapping;
- delivery, `scan`, `dump` and the TUI header all identify the audience so a
  human can tell private from deliberately-shared work.

## CLI

    send --to X --to Y            multi-recipient; repeatable
    send-notice                   global, unchanged
    send-notice --scope baton.*   scoped

A wildcard is refused wherever an exact participant is required, and `--to`
never accepts one. That is a validation rule, not a parsing accident, and it
gets its own test with `--to baton.*`.

## Order

1. selector grammar and expansion, pure, testable without a store;
2. `notice_audience`, scoped and global notices through one path;
3. `see`/`wait` delivery by audience membership;
4. multi-recipient publication, atomic, shape A;
5. possible-duplicate publication warning;
6. CLI;
7. TUI audience display and picker;
8. docs, rebuild.

Steps 1-3 are independent of the shape decision and can land first.

## Decisions

- Publication remains at-least-once in protocol 10; ambiguous retries may be
  sender-marked `possible_duplicate`. No token is added in this stage.

Global-notice freezing is no longer open: Slawomir ruled on 2026-08-10 that
the configured recipient set freezes at publication.

Shape A is ruled. The selector grammar is built and tested, being pure and
explicitly cleared to start; nothing else has begun.

One reading I made rather than quoted: `baton.*` matches DEEPER addresses
such as `baton.a.b`, not only `baton.<role>`. The ruling gives two-segment
examples and does not say. A scope names a domain and everything under it is
in it; the alternative would make an announcement silently skip a participant
every reader would expect to be included. Flagged rather than buried.

## Not built at the WIP checkpoint (2026-08-10)

Recorded here rather than left in a review thread, because these are pins this
plan made and the checkpoint does not meet them. Stage 2.2 is NOT complete.

- `Store.reply` creates its response message with no publication record, so
  every reply delivers `audience: []`. The requirement is in this plan --
  "Response messages created by `reply` also receive their own
  single-recipient publication record" -- and had no test.
  See `work/finding-orphan-publication-link/`.
- The multi-recipient return shape pinned above ("`publication_id` and the
  recipient-to-message mapping") is not returned. `send` returns the
  publication id alone for several recipients, so the mapping exists nowhere
  the caller can see and nothing tests it.
- The single-recipient return pinned as "unchanged, plus `publication_id`" is
  still the bare message id. Delivery carries the audience but not the
  publication id.
- `messages.publication_id` is nullable with no `doctor` check, so the two
  gaps above are invisible to the instance's own diagnosis.

What IS built and break-checked: selector grammar and expansion, frozen
notice audiences global and scoped, delivery by membership, multi-recipient
publication with independent lifecycles, the `possible_duplicate` warning on
both at-least-once paths, audience on directed delivery, console display, CLI
and documentation.

## Queued child — TUI scoped-notice audience picker (2026-08-11)

`findings/finding-tui-notice-scope-picker/` records the confirmed authoring
gap: core and CLI accept `--scope 'lang.*'`, but the console's `N` flow calls
`send_notice` without a scope and can publish only globally. The child was
initially implementation-ready under the closed-picker proposal; the UX
supersession below makes the exact-participant meaning the one remaining
product clarification. It does not reopen approved core scope semantics.

### UX supersession — 2026-08-11

The child's original closed, registry-derived picker is superseded by an
editable filter/combobox. Typing narrows configured team-scope suggestions,
but a complete typed scope such as `web.*` can be submitted directly and is
validated/expanded only by the core. Slawomir resolved the exact-participant
edge: the choices are `*` (global) and configured `team.*` values only. Exact
participants remain ordinary directed messages and never appear in this
notice control.

## Current actionable state — 2026-08-11

The earlier WIP checkpoint and its “not built” bullets are **superseded as
current state** and retained only to show how the implementation reached the
released protocol-10 result. Baton 1.0.0 contains the core/CLI Stage 2.2 work,
including the later orphan-publication corrections and public result shapes.

The TUI scoped-notice child is implemented and reviewer-approved for 1.1; see
its FINDING, PLAN, PROGRESS, and newest append-only review at
`findings/finding-tui-notice-scope-picker/review-2026-08-11T15-55-03Z.md`.
No implementation step remains in this parent. After the 1.1 child is committed,
the parent and child are eligible for Slawomir's deliberate ephemeral-finding
cleanup pass.
