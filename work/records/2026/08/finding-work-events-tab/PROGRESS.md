# Progress — the Work Events play-by-play

Owned exclusively by the implementer (`baton.claude` under v11).

## Step 1 — W123 implemented (2026-08-17)

Claimed W123. Revalidation confirmed the pinned boundary: no schema
change is needed, because the immutable `events` rows already carry
sequence, typed kind, actor, timestamp, structured payload and act
references. The gap was that the global read is not Work-relative, says
nothing about WHY an event belongs to a Work, and has no claim
intervals.

### The association matrix is typed, never a string search

`_EVENT_SUBJECT_KINDS` attaches on `payload.work`. Creation is the one
exception and it matters: the created id is the act's RESULT, not one of
its inputs, so the payload has no `work` key at all and the join is the
Work's own `created_seq`. Creation additionally attaches to its `parent`
and `follow_up_of` — found during testing, since my first predicate only
matched the created Work and a parent could not see its child being
born. Dependency and acceptance acts genuinely affect two Works and
attach to both from the SAME event with direction-specific roles, which
is the finding's "storage is not duplicated".

The alternative — scanning payloads for a Work-shaped string — is
explicitly refused, and there is a regression for exactly that: a
release whose *rationale quotes another Work's id* must not manufacture
an event on that bystander.

Excluded by ruling: `post_message`, `mark_seen`, `create_thread`,
`accept_config`. Workflow-bearing message acts (`request`, `respond`,
`dispose`, trial lifecycle, `revise_work`) are their own kinds and stay
in, without duplicating any message body.

### Claim intervals

A `claim` opens an interval; the first later event that releases it
closes it — explicit release, pass/return, terminal close, entry into
waiting or parked, or a gate that invalidated the claim. That last case
is read from the typed `released_claims` payload the authority already
records, not inferred. Heartbeats are liveness evidence INSIDE the
interval and never restart it or fabricate work time. The interval rides
BOTH boundary events, so the same facts are reachable from either end.

### Surfaces

`work-events work=W [after=|before=|newest=|limit=]` reuses W76's
pagination contract exactly, proof row included, so an exactly full
final page never advertises a continuation that opens empty. JSON pages
stay canonical ascending.

The TUI gains `Messages`/`Events` tabs with Messages default and the
active tab bracketed; `]`/`[` switch from anywhere in Work detail; the
footer ALWAYS advertises `[/] tabs`. Events has its own `E<seq>` index
and reader in wide split and narrow stack, opens newest-first like
Messages, and `Ctrl-W` stays pane-local to the active tab. Per-tab
focus, selection, page cursor and reader scroll live in separate fields,
so switching preserves both sides by construction rather than by saving
and restoring one shared slot.

### Evidence

New `tests/work/test_w123_work_events.py` (25): the subject matrix; the
typed-not-string-search proof; the dependency act read from both ends
with opposite roles and its rationale; creation naming parent and
predecessor; discussion and cursor movement staying out; workflow-
bearing acts staying in without bodies; completed intervals on both
boundaries; heartbeats neither restarting nor extending; pass, close,
park, waiting and an invalidating gate each ending an interval;
bidirectional bounded paging walked to exhaustion; the exact-limit
boundary; canonical ascending JSON; the always-visible tab bar and
footer hint; both bracket keys; switching from every pane; per-tab
state preservation; pane-local Ctrl-W; newest-first Events;
roles/related/payload in the reader; navigation writing nothing; and
conversational counts untouched.

Break-sweeps: restarting the interval on a heartbeat reds 2; removing
the active-tab distinction reds 3; admitting conversation to the
journal reds 1.

That last sweep initially did NOT red, and the reason is worth keeping:
a plain post and a seen mark both record `payload.work = None`, so the
association predicate excluded them regardless of the kind list — the
behavioural assertion passed for the wrong reason. The test now also
asserts the exclusion list directly, which is what actually holds the
line. Noted in the test itself so the structural half is not later
deleted as redundant.

`docs/BATON-WORK.md` documents the tabs, the key hints, the journal's
scope, and the JSON verb.

## Step 2 — W123 R1: five review defects corrected (2026-08-17)

Round one requested changes on four typed relationships plus one
obsolete documentation sentence. All five reproduced from the committed
tree before any edit; the review was right on every point.

**R1 — creation did not name what it created.** `_event_related` looked
for `payload.created`, which does not exist. I had written that guess
myself, and it is exactly the mistake the finding's own "typed, never a
string search" rule exists to prevent: the created id is the act's
RESULT, carried by the Work row whose `created_seq` is the event. A
parent or predecessor could see that a birth happened but not which
child. Resolved through that typed relation, in one query per page.

**R2 — the survivor never saw its duplicate.** The roles and related
logic were already written, but the SQL predicate never selected a
`close_work` by `payload.duplicate_of`, so the branch was unreachable.
Now attached, in both directions: the closed Work names the survivor it
was folded into (`duplicate_target`), and the survivor names the Work
that was rejected as its duplicate (`duplicate`).

**R3 — open claims had no ongoing duration.** `elapsed_seconds` stayed
`None` until an end event existed, so a client could not show how long a
live claim had been held. It is now computed from the read's own
instant; `started_at` stays fixed and a heartbeat still changes nothing.
The TUI reader says `still open, held Ns` instead of just `still open`.

**R4 — accept-created providers did not reach their parent.** Like R1,
the parent link is a typed relation on the provider's Work row, not a
payload key.

R4 also produced the one place my own fix was wrong, and the review's
required negative case is what caught it. My first predicate matched on
the provider's CURRENT parent, so `accept into=existing` reached that
provider's pre-existing parent — a relation that is real but that this
act did not create. My scratch probe missed it because the provider I
built there happened to have no parent. The predicate now requires the
provider's `created_seq` to be this very event, so only an accept that
CREATED its provider reaches the parent it placed it beneath.

**R5 — the docs prescribed two entry behaviours.** The paragraph said
the index opens newest-first and, a sentence later, that selecting a
Thread opens its first personal-new message. W76 superseded the second.
Removed, and replaced with the newest-Message rule and the reason it is
also the newest unseen one.

### Evidence

Six new regressions in the W123 module (now 31): a parent seeing which
child was born and the child's reciprocal view; a predecessor seeing its
follow-up; the duplicate relation in both directions; an accept-created
provider reaching its parent with the consumer's view unchanged; the
negative `into=existing` case proving no parent relation is invented;
and an open claim's ongoing duration across a heartbeat and across an
advancing clock, with `started_at` pinned.

The fixture gained a real second team, because the accept flow is
cross-team convergence and a same-team stand-in would not have
exercised it.

Break-sweeps: reverting R1 reds 2; R2 reds 1; R3 reds 1; loosening R4
back to the current-parent match reds 1.
