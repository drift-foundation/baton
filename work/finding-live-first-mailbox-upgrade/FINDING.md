# Live-first mailbox upgrade: availability is the migration invariant

Folder: `work/finding-live-first-mailbox-upgrade/`
Requirement from Slawomir, relayed and scoped by the reviewer, 2026-08-07.
Recorded separately so it is not entangled with the damaged-attachment work
it arose alongside, and **not to be broadened while communications are
live**.

## The failure to prevent

This deployment could not coordinate for **more than ten hours**.

The cause was an in-place protocol migration. It stalled awaiting review;
every team stayed blocked; and the channel needed to unblock it was the
channel that was blocked. The implementer sat through six consecutive
fifty-minute waits reporting no movement on a queue he had jammed, waiting for
a review that could not reach him.

The mechanics of that migration were sound and rehearsed. The error was
treating the coordination channel as a resource that could be spent to protect
historical continuity — when it was the resource every actor needed in order
to do anything at all, including reviewing the change that was consuming it.

## The invariant

**Channel availability outranks preservation of pending or historical
messages.**

Historical continuity is secondary. Once communication works, actors identify
and re-send whatever still matters — which is cheap. A jammed coordination
channel is expensive precisely because working around it requires the channel.

## Contract

- A bounded, short outage is the primary invariant.
- Retire the previous mailbox **intact**.
- Initialize and **verify** a fresh target-protocol mailbox at the canonical
  path immediately (`doctor ok: true` before proceeding).
- Reconnect actors and let them re-send whatever still matters.
- Historical message porting is **optional, offline, and must never block the
  live channel** — performed only when someone demonstrates a need.

## Status

**Documented, not engineered.** The procedure is `RUNBOOK.md` beside this
file, kept here because it is live operational doctrine rather than a record
of finished work. The fast fresh-instance cutover *is* the runbook: the
in-place procedure was demoted to a separate document and then removed
outright, along with the migration code it described, so the invariant is now
enforced by the tool having no in-place path to reach for. `migrate` is an
audited refusal that gains a path only alongside a future protocol bump.

That satisfies the runbook half of the requirement. The architecture half is
open.

## Open: make the safe path the easy path

Today the fast path is a documented manual sequence — stop listeners, move the
directory aside, write a config, `init`, `doctor`, broadcast. Nothing enforces
the ordering, records what was retired, or verifies the new instance before
anyone is told to reconnect. The disciplined operator gets it right; a hurried
one during an incident may not, and an incident is exactly when it will be run.

A plausible shape, **not designed and not started**: a first-class audited
ceremony that quiesces the current instance, moves it aside with its identity
and integrity recorded, and reports precisely what to initialize — so the
retirement is an operation with an audit trail rather than a `mv`.

Deliberately deferred, and still not started. It was held back while the
protocol-7 implementation was under review; that review has since completed
and been accepted for commit, so the reason to hold is now simply that it is
unstarted new surface, not that it would stack on unreviewed work. It must not
be attempted while communications are live.

## Historical porting: not designed, and not to be

Ruled by Slawomir, relayed by the reviewer (`decision`, outcome
`deferred_optional`): **do not specify or implement message porting** — not as
part of this finding, and not before the protocol-7 review lands.

Most old messages never need porting. Once communications are live, actors
identify and re-send the small subset that still matters. At this cutover the
retired mailbox stayed intact for inspection. **Archival completeness must not
become a new dependency of the live channel.**

If someone ever demonstrates an actual need, it gets its own
`work/finding-.../` folder at that point. Until then there is nothing here to
build, schedule, or track, and this section exists only to say so — an earlier
draft listed design questions for a port, which read like an agenda and has
been removed for that reason.

**Superseded 2026-08-25:** the protocol 6, 7, and 8 mailbox archives were
approved for deletion after v11 replaced every fallback consumer. Their old
messages will no longer be recoverable. No port was requested or needed.

## This deployment, for the record

- Retired intact at the time; deletion approved on 2026-08-25
  (uuid `0231b16a81ef2522d630e8d1a81d8c97`, protocol 6, generation 2,
  59 messages, 273 transitions, `quick_check: ok` — verified read-only).
- Fresh protocol-7 instance at the canonical path, uuid
  `1063b97dbba0ed1382ae386bb9f9240f`, `doctor ok: true`.
- No port performed. Nobody has needed one.
- At the time, the protocol-6 executable
  (`cf2de45ef5963daec6a63806fbfacf0638e4d450e8c5fa08b081d596018977c9`) was the
  only thing that could read the retired authority.

## Cutover record

The contract has now been exercised twice in one day, both times without an
in-place migration and both times with the retired instance preserved whole.

| Retired | Initial disposition | Live then |
|---|---|---|
| protocol 6 | archived intact; deletion approved 2026-08-25 | — |
| protocol 7 | archived intact; deletion approved 2026-08-25 | — |
| protocol 8 | archived intact; deletion approved 2026-08-25 | protocol 9 |

What made the last cutover cheap, and is worth repeating:

- **Both breaking changes rode one protocol bump.** The typed content envelope
  was pinned to land inside protocol 8 before that authority was ever
  initialized, so it cost one teardown rather than two.
- **Participants were stood down deliberately before the swap**, with active
  claims disposed first. Zero claims were active at retirement, so nothing was
  orphaned.
- **The ledger was read before retiring** to establish who was actually on the
  channel. Only two participants had ever transacted, which is what made the
  outage window a non-event.
- **Undelivered messages were enumerated, then re-sent by hand** on the new
  authority. One message was stranded and one was re-sent.
- **Retirement is a rename, never a delete**, so every cutover so far remains
  reversible and inspectable.

The step that still hurts: reconnect instructions cannot travel through the
channel being replaced. The broadcast can only be published after the new
authority exists, so every participant needs an out-of-band nudge. That is the
gap `work/finding-human-console/` closes for the human, and it is the reason
the deployment path is versioned (`baton-protocol9/`) rather than overwritten
in place — an agent still pointing at the old executable fails closed with a
protocol error instead of silently reading a dead mailbox.
