# Offline migration procedure — in-place protocol 6 → 7 on a COPY

Status: **not approved for execution**, and not needed by this deployment —
the live instance was created fresh at protocol 7, so there is no in-place
cutover to perform here.

The two hardening findings that once blocked it are now implemented and
reviewed:

- `work/finding-maintenance-entry-claim-race/` — implemented for protocol 7.
  The protocol-6 source-side entry check remains explicitly deferred, so on
  that one path the preflight scan is the only guard.
- `work/finding-crash-durable-migration-publication/` — implemented.

Before running this against any real instance, re-read both and confirm the
deferred protocol-6 gap is acceptable for that instance.

> **This is NOT the migration runbook.** The primary procedure is the fast
> fresh-instance cutover in `RUNBOOK.md`. Availability of the coordination
> channel outranks preservation of pending or historical messages, so a live
> deployment is never migrated in place.
>
> What follows is the procedure for migrating an instance **off the live**
> path: a retired authority being repaired for archival, an optional state
> port, or another deployment’s protocol-6 instance being upgraded on its own
> schedule. Applied to a copy, none of it costs availability.
>
> It was written as a live cutover plan and used as one — that was the
> mistake. See "Why this is not the primary path" below.

## Why this is not the primary path

In-place migration maximizes historical continuity and minimizes moving
parts, which is why it was chosen. What it also does is make the entire
deployment unable to coordinate for the whole duration — **including the
review of the migration itself**.

That is not hypothetical. During this incident the suite could not coordinate
for more than ten hours: the cutover stalled awaiting review, every team was
blocked, and the channel needed to unblock it was the blocked channel. The
implementer spent six consecutive fifty-minute waits reporting no movement on
a queue he had jammed.

Pending messages are cheap to re-send. A jammed coordination channel is not
cheap to work around, because the workaround needs the channel.

## Two pinned executables

`bin/baton` in the repository is now **protocol 7**, and a protocol-7
executable **cannot open a protocol-6 instance at all** — config validation
rejects `protocol_version: 6` before anything else runs. So the deployed
`/home/sl/src/baton/bin/baton` currently returns exit 4 against the live
instance. That is a consequence I caused by rebuilding the deployed artifact
ahead of the cutover; it is tolerable only because teams are already stood
down.

**Protocol-6 executable** — use for all live-instance work through step 3:

    /home/sl/src/baton-protocol6/bin/baton
    baton 1.0.0 (protocol 6)
    bin/baton                cf2de45ef5963daec6a63806fbfacf0638e4d450e8c5fa08b081d596018977c9
    AGENTS-MAILBOX-PROTO.md  3705b3e16f0c5b83f2821a841a95c027bba97895b3afe8e670e449b398d86d23

**Protocol-7 executable** — use from step 4 onward:

    /home/sl/src/baton/bin/baton
    baton 2.0.0 (protocol 7)
    bin/baton                3ca7bd083c9dcc0c62a5c54e22b66b6c5a311a873e6b1d5d71f141f82623b2bb
    baton_v6.py              e14e94bf262e673cf0dc0e230c5ec00e9f612b80135006b4878320a98b625b5a
    AGENTS-MAILBOX-PROTO.md  d13216714e4b79b186daa8e93acca3f960c2d0e0507d5e15e5fe5555fae60ee7

Verify both with `sha256sum` before starting. The fallback is a recovery
dependency and must not be unpinned.

The protocol-6 fallback is 1.0.0, which predates phase 1's skip-and-continue,
so `baton.reviewer`'s plain `wait` stays blocked by the two damaged messages
until the migration completes; use `claim --message-id` in the meantime.

## Rehearsed end-to-end on a copy of the live instance

Every step was executed on a byte copy of the real `mailbox.sqlite3` and
`baton.json` with their WAL siblings. Results: 55 messages preserved;
`doctor` `ok: true` after recovery with `problems: []` and three quarantined
warnings; the snapshot reopened cleanly under the protocol-6 executable as
protocol 6, generation 2, 55 messages.

## Step 1 — drain, BEFORE gating

`close` and `reply` are themselves gated by maintenance, so claims cannot be
drained once the gate is set. Drain first.

    P6=/home/sl/src/baton-protocol6/bin/baton
    C=/home/sl/src/mailbox/baton.json
    $P6 --config $C scan

Every entry under `claimed` must be resolved by **its own holder** (`reply` or
`close`) — claim ownership is actor+seed bound and cannot be resolved on
someone else's behalf. A dead holder needs `recover-claim`. Repeat `scan`
until `claimed` is `[]`.

A claim can still appear between this check and the gate. In protocol 7 that
race is closed by `maintenance-enter` itself, which refuses atomically with
`EXIT_RACE` and leaves the instance **ungated** so the holder can still drain.
The migration re-checks in its own transaction as defence in depth.

**The preserved protocol-6 executable does not have that entry-time check**
(deferred by Slawomir, see `work/finding-maintenance-entry-claim-race/`), so on
the step-2 entry below the scan above is the only guard. Repeat it immediately
before gating.

## Step 2 — enter maintenance, with the PROTOCOL-6 executable

    $P6 --config $C maintenance-enter \
      --participant human.slawomir --actor slawomir --seed <SLAWOMIR-SEED> \
      --reason "protocol 7 upgrade"

The protocol-7 executable cannot open the instance yet, so this must be the
protocol-6 one.

## Step 3 — stage the generation-3 config and publish it atomically

The config carries `protocol_version`, so it moves with the schema. Generate
it from the current file rather than hand-editing, so the diff is exact by
construction, and publish with `os.replace` so no partial file is ever visible:

**Take the rollback copy FIRST**, under a name `os.replace` will not consume,
and make it durable before anything is overwritten:

    cp /home/sl/src/mailbox/baton.json /home/sl/src/mailbox/baton.json.gen2
    sync /home/sl/src/mailbox/baton.json.gen2 /home/sl/src/mailbox

Then stage and publish, fsyncing the staged file **before** the rename and the
directory **after** it. Without both, a crash can leave a protocol-7 database
with no durably published matching config:

    python3 - <<'PY'
    import json, os
    src = "/home/sl/src/mailbox/baton.json"
    cfg = json.load(open(src)); before = dict(cfg)
    cfg["protocol_version"] = 7
    cfg["generation"] = 3
    diff = {k for k in set(before) | set(cfg) if before.get(k) != cfg.get(k)}
    assert diff == {"protocol_version", "generation"}, diff

    staged = src + ".staged"
    with open(staged, "w") as handle:
        json.dump(cfg, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())          # contents durable BEFORE the rename
    os.replace(staged, src)                 # atomic swap
    dirfd = os.open(os.path.dirname(src), os.O_DIRECTORY)
    try:
        os.fsync(dirfd)                     # the rename itself durable
    finally:
        os.close(dirfd)
    print("published; diff was exactly", sorted(diff))
    PY

The earlier version of this step fsynced neither, and its rollback line
referenced `baton.json.staged` *after* `os.replace` had already consumed that
pathname — so it preserved nothing at all. Both are fixed above: the copy is
taken before the swap, from a name that survives it.

This is not a forbidden hand-edit: `regen` and `migrate` are the two audited
ceremonies that accept a new config, and `migrate` accepts this one inside the
same transaction that moves the schema. The migration independently verifies
the diff — it reconstructs the accepted config by setting `generation` and
`protocol_version` back and refuses unless that reproduces the accepted
digest, so any other change fails closed.

## Step 4 — migrate, with the PROTOCOL-7 executable

    P7=/home/sl/src/baton/bin/baton
    $P7 --config $C migrate \
      --participant human.slawomir --actor slawomir --seed <SLAWOMIR-SEED> \
      --snapshot-dir /home/sl/src/mailbox-pre7-snapshot

`--snapshot-dir` is how the backup is taken. The migration drains the WAL,
publishes a hash-verified fsynced copy of the database **and the reconstructed
generation-2 protocol-6 config**, then opens and validates that copy before
touching anything. A hand-rolled `cp` of a WAL database is not a coherent
backup, and the only executable that can open the pre-migration instance has
no snapshot verb — so the migration takes its own.

Expected:

    {"migrated": true, "from_protocol": 6, "protocol": 7,
     "messages_preserved": <N>, "accepted_generation": 3,
     "snapshot": {"protocol": 6, "accepted_generation": 2,
                  "messages": <N>, "active_claims": 0, ...}}

`snapshot.messages` must equal `messages_preserved`; the migration refuses to
report success otherwise. It also refuses if any claim is active, if the row
count changes, if a foreign key is violated, or if the resulting schema is not
byte-exact protocol 7 — the last check runs *before* commit, so a mistaken
rebuild rolls back rather than becoming the authority.

If the response is lost, re-running is safe: a completed migration returns
`{"migrated": false, ...}`.

## Step 5 — recover the three damaged records, GATE STILL CLOSED

**Requires Slawomir's separate explicit approval.**

    ID="--participant human.slawomir --actor slawomir --seed <SLAWOMIR-SEED>"

    $P7 --config $C quarantine-attachment da19ba84c2503ae9d7c4354609097550 $ID \
      --reason "delivered and closed; retained pin went stale after publication"

    $P7 --config $C quarantine-attachment b1894f68fa4885cbe2e749d977afac7f $ID \
      --reason "never delivered; attachment edited after publication"

    $P7 --config $C quarantine-attachment 9cff508bcf03ef05a42f02e83a6609f3 $ID \
      --reason "never delivered; attachment edited after publication"

The first returns `prior_state: "closed"` and `state: "closed"` — an
acknowledgement, because that message really was delivered and only its
retained pin went stale, so its history is not rewritten. The other two return
`pending → quarantined`.

Quarantine is explicitly authorized under a plain maintenance gate (and
refused during a move), so this runs before participants are let back in.

## Step 6 — verify healthy, still gated

    $P7 --config $C doctor

Must report `ok: true`, `problems: []`, the three ids under `quarantined`, and
three warnings naming them as damaged-but-quarantined. Message counts must
match step 4's `messages_preserved`, with two rows moved from `pending` to
`quarantined`.

Do not proceed if anything else appears.

## Step 7 — reopen

    $P7 --config $C maintenance-exit \
      --participant human.slawomir --actor slawomir --seed <SLAWOMIR-SEED> \
      --reason "protocol 7 upgrade complete"

From here `/home/sl/src/baton/bin/baton` is the correct executable for
everyone.

**Do not delete `/home/sl/src/baton-protocol6/`.** It is the only executable
that can read a retired protocol-6 authority, and a retired mailbox is kept
indefinitely. An earlier version of this step said it could be removed once
the migration was confirmed good; that was wrong.

## Step 8 — announce

Broadcast a completion notice. It persists for its TTL and, since the
wait/notice fix, is delivered through `wait` as well as `see`, so teams that
restart later still receive it. Tell them to use
`/home/sl/src/baton/bin/baton`.

## Rollback

**Before step 4 commits:** nothing to undo. The migration is one transaction
and self-validates before committing; on failure the instance is still a
working protocol 6. Restore the generation-2 config from the snapshot and
resume with the protocol-6 executable:

    cp /home/sl/src/mailbox-pre7-snapshot/baton.json /home/sl/src/mailbox/baton.json

**After step 4 commits:** restore both files from the snapshot, with the
instance quiet and no process holding it open. The snapshot's database was
checkpointed before copying, so the main file is self-contained and the stale
siblings must be removed rather than replayed over it:

    rm -f /home/sl/src/mailbox/mailbox.sqlite3-wal /home/sl/src/mailbox/mailbox.sqlite3-shm
    cp /home/sl/src/mailbox-pre7-snapshot/mailbox.sqlite3 /home/sl/src/mailbox/
    cp /home/sl/src/mailbox-pre7-snapshot/baton.json      /home/sl/src/mailbox/
    $P6 --config $C doctor      # protocol 6, generation 2

Verified in rehearsal: the snapshot reopens under the protocol-6 executable as
protocol 6, generation 2, with every message intact.
