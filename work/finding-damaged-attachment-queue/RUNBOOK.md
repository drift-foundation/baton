# Baton migration runbook — fast fresh-instance cutover

**This is the primary and default procedure for any Baton protocol
migration.** Availability of the coordination channel is the invariant.

The in-place migration procedure lives in `RUNBOOK-offline-migration.md` and
is **never** used on a live deployment. It applies only off the live path: a
retired authority being repaired for archival, an optional state port, or
another deployment upgrading on its own schedule.

## The invariant

**Channel availability outranks preservation of pending or historical
messages.**

Porting old messages is **optional and not on the critical path**. In most
incidents nobody needs them: once communication works, actors identify and
re-send whatever still matters. Ported history is a separate, optional
recovery operation, performed only when someone demonstrates a need, and never
while blocking live communication.

Established by Slawomir after this deployment could not coordinate for more
than **ten hours** during an in-place cutover. That is not an acceptable
migration mode.

## Contract

- Keep the outage short and bounded.
- Retire the previous mailbox **intact**.
- Bring up a **verified empty** target-protocol mailbox at the canonical path
  immediately.
- Let actors reconnect and re-send needed work.
- Port historical messages only on demonstrated need, never while blocking
  live communication.

## Procedure

Target: minutes of downtime. Nothing below waits on a review, an approval
cycle, or a schema transformation.

### 1. Quiesce and set the old mailbox aside, intact

Use the executable that matches the **current** instance's protocol.

    OLD=/home/sl/src/mailbox
    RETIRED=/home/sl/src/mailbox-retired-protocol<N>-<UTC timestamp>

Stop listeners, then move the whole instance directory aside. Move, do not
copy-and-delete, and do not edit it afterwards — the retired mailbox is an
**immutable recovery artifact**, kept indefinitely and never written to.

Record what you retired, so it can be identified and read later if anyone ever
needs to. This is provenance, not a queued task:

    <retired path>   uuid <...>   protocol <N>   generation <G>
    <M> messages   <T> transitions   quick_check: ok

Verify `quick_check` read-only before declaring it good.

### 2. Initialize and verify a fresh instance at the canonical path

    B=/home/sl/src/baton/bin/baton
    C=/home/sl/src/mailbox/baton.json

Write the config for the target protocol — same participants, roots and
`retention_days` as the retired one, `generation: 1`, `protocol_version` at
the new protocol — then:

    $B --config $C init
    $B --config $C doctor

**`doctor` must report `ok: true` with `problems: []` before you proceed.** A
fresh instance that is not verifiably healthy is worse than the outage.

### 3. Reconnect and announce, immediately

Broadcast a notice on the new instance stating:

- that the previous mailbox was retired and history is **not** carried
  forward, so re-send anything still needed;
- the exact executable and config path to reconnect with;
- that the older executable must not be used against the new instance;
- that the older executable must **not be deleted**, because it is the only
  thing that can read the retired authority.

Notices persist for their TTL and are delivered through `wait` as well as
`see`, so teams that reconnect later still receive it.

Then send a durable directed message to each participant that had work in
flight, so a reconnecting actor finds a claimable instruction rather than only
a broadcast.

### 4. Confirm service, then stop

Coordination is restored at this point, and the cutover is **done**. Do not
continue into a repair, a schema exercise, or anything else while people are
using the channel you just brought back.

## Historical state: there is no port, by decision

The cutover is **complete** at step 4. Porting old messages is not a step, not
a follow-up, and not a completion criterion.

Slawomir's ruling: do not specify or implement porting. Most old messages never
need it — once communications are live, actors identify and re-send the small
subset that matters, and the retired mailbox stays intact for inspection.
**Archival completeness must not become a dependency of the live channel.**

If someone ever demonstrates an actual need for specific historical messages,
that gets its own finding at that time. Until then: read the retired mailbox
directly with the executable matching its protocol. Do not improvise a port
against a live authority — unvalidated rows in the single transactional
authority would be a worse failure than the outage such a port would be trying
to undo.

## What this deployment did, 2026-08-07

Executed as above, by the reviewer, after the in-place cutover stalled:

- Retired intact to
  `/home/sl/src/mailbox-retired-protocol6-20260807T1249Z`
  (uuid `0231b16a81ef2522d630e8d1a81d8c97`, protocol 6, generation 2,
  59 messages, 273 transitions, `quick_check: ok` — verified read-only).
- Fresh protocol-7 instance at `/home/sl/src/mailbox/`,
  uuid `1063b97dbba0ed1382ae386bb9f9240f`, `doctor ok: true`.
- Reset notice broadcast; participants reconnected and re-sent.
- No port performed. Nobody has needed one.

Consequences worth carrying forward: the three damaged attachment records are
in the retired archive, not the live channel, so live `doctor` is `ok: true`
and their repair is unhurried and optional. The protocol-6 executable at
`/home/sl/src/baton-protocol6/bin/baton`
(`cf2de45ef5963daec6a63806fbfacf0638e4d450e8c5fa08b081d596018977c9`) is now the
only way to read the retired authority and must be preserved.
