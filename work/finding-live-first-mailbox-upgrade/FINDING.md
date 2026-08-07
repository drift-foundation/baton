# Live-first mailbox upgrade: availability is the migration invariant

Folder: `work/finding-live-first-mailbox-upgrade/`
Requirement from Slawomir, relayed and scoped by the reviewer, 2026-08-07.
Recorded separately so it is not entangled with
`work/finding-damaged-attachment-queue/`, and **not to be broadened while
communications are live**.

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

**Documented, not engineered.** The procedure is `RUNBOOK.md` in
`work/finding-damaged-attachment-queue/`, which was restructured so the fast
fresh-instance cutover *is* the runbook. The in-place procedure was first
demoted to a separate off-live document and has since been removed outright,
along with the migration code it described — the invariant is now enforced by
the tool having no in-place path to reach for.

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
identify and re-send the small subset that still matters, and the retired
mailbox stays intact for inspection. **Archival completeness must not become a
new dependency of the live channel.**

If someone ever demonstrates an actual need, it gets its own
`work/finding-.../` folder at that point. Until then there is nothing here to
build, schedule, or track, and this section exists only to say so — an earlier
draft listed design questions for a port, which read like an agenda and has
been removed for that reason.

The standing answer to "can we get the old messages back" is: the retired
mailbox is intact and readable, so yes — later, offline, if it turns out to
matter.

## This deployment, for the record

- Retired intact:
  `/home/sl/src/mailbox-retired-protocol6-20260807T1249Z`
  (uuid `0231b16a81ef2522d630e8d1a81d8c97`, protocol 6, generation 2,
  59 messages, 273 transitions, `quick_check: ok` — verified read-only).
- Fresh protocol-7 instance at the canonical path, uuid
  `1063b97dbba0ed1382ae386bb9f9240f`, `doctor ok: true`.
- No port performed. Nobody has needed one.
- The protocol-6 executable
  (`cf2de45ef5963daec6a63806fbfacf0638e4d450e8c5fa08b081d596018977c9`) is the
  only thing that can read the retired authority and must be preserved.
