# Baton migration runbook — fast fresh-instance cutover

**This is the primary and default procedure for any Baton protocol
migration.** Availability of the coordination channel is the invariant.

There is no in-place migration procedure. The 6 → 7 path and its runbook
were removed once this deployment moved to a fresh protocol-7 instance, so
the availability-first cutover below is not merely the preferred option — it
is the only one the tool supports. `migrate` is an audited refusal that gains
a path only alongside a future protocol bump.

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

## Cutover record

This procedure has been executed three times, all on 2026-08-07: 6 to 7 (by
the reviewer, after an in-place cutover stalled), 7 to 8, and 8 to 9. Each
retirement, its archive path and what it preserved are tabulated in
`FINDING.md` beside this file.

No port was ever performed. Nobody has needed one — which is the invariant
above holding in practice rather than in theory.

## Preserve the executable of every retired era

**A retired authority can only be read by the executable of its own
protocol.** Schema validation is exact, so a newer build refuses an older
instance rather than misreading it: a protocol mismatch exits 4, and schema
tampering within a matching protocol exits 6. Both fail closed, and neither
gives you the data.

Each versioned deployment directory is therefore the only key to its archive
and must not be deleted:

| Archive | Readable only by |
|---|---|
| `mailbox-retired-protocol6-20260807T1249Z` | `baton-protocol6/bin/baton` |
| `mailbox-protocol7-retired-20260807` | the protocol-7 build |
| `mailbox-protocol8-retired-20260807T234737Z` | `baton-protocol8/bin/baton` |

This is why the deployment path is versioned rather than overwritten in place.
It also means an agent still pointing at an old path fails closed on a
protocol error instead of silently reading a dead mailbox — the failure mode
worth having.

Also carried forward: damaged attachment records left in a retired archive are
not on the live channel, so live `doctor` stays `ok: true` and their repair is
unhurried and optional.
