# Baton — portable coordination over one transactional authority

Baton is a standalone coordination tool for agents and humans, providing
role-addressed handoffs, broadcast notices, and audited administrative
operations over a single SQLite database. It has no dependency on any host
project; every instance is defined entirely by one explicitly passed
strict-JSON config.

## How a team uses Baton

A team gives each participant a scoped address such as `team.implementer` or
`team.reviewer`. The implementer publishes a handoff to the reviewer. One
reviewer claims it, completes the review, and replies through the same
transactional channel. The implementer then receives that response. Baton
records who claimed and completed each handoff, prevents two consumers from
owning the same work, and preserves durable reports for later inspection.

Addresses are not limited to implementation and review. A deployment can add
participants such as `team.security`, `team.release`, or `org.lead` without
changing the protocol. Broadcast notices provide status updates that every
participant may see but nobody claims.

## Quick example

The included example config defines an implementer, a reviewer, and a lead.
Create a temporary mailbox instance:

    BATON="$PWD/bin/baton"
    DEMO=/tmp/baton-demo
    mkdir -p "$DEMO"
    cp example-baton.json "$DEMO/baton.json"
    "$BATON" --config "$DEMO/baton.json" init

The implementer publishes a durable handoff:

    IMPLEMENTER_SEED=22222222222222222222222222222222
    printf '%s\n' '# Handoff' 'The implementation is ready for review.' > "$DEMO/handoff.md"
    "$BATON" --config "$DEMO/baton.json" send \
      --participant team.implementer --actor implementer-1 --seed "$IMPLEMENTER_SEED" \
      --to team.reviewer --kind implementation_handoff --retention durable \
      --body "$DEMO/handoff.md"

The reviewer waits for work. `wait` prints the claimed message and its
`claim_id` as JSON:

    REVIEWER_SEED=11111111111111111111111111111111
    "$BATON" --config "$DEMO/baton.json" wait \
      --participant team.reviewer --actor reviewer-1 --seed "$REVIEWER_SEED"

After reviewing, copy that `claim_id` into the reply command:

    CLAIM_ID="paste-claim-id-here"
    printf '%s\n' '# Review' 'Approved.' > "$DEMO/review.md"
    "$BATON" --config "$DEMO/baton.json" reply "$CLAIM_ID" \
      --participant team.reviewer --actor reviewer-1 --seed "$REVIEWER_SEED" \
      --kind review --outcome approved --retention durable \
      --body "$DEMO/review.md"

The implementer receives the response with the same participant identity used
to send the handoff:

    "$BATON" --config "$DEMO/baton.json" wait \
      --participant team.implementer --actor implementer-1 --seed "$IMPLEMENTER_SEED"

### Quick inline messages

Short ACKs, pings, and decisions do not need temporary files. Pass `--body -`
and pipe the bytes on standard input (`send` and `reply` also default their
body to stdin):

    printf '%s\n' "I'm still working and testing; give me more time." | \
      "$BATON" --config "$DEMO/baton.json" send-notice \
      --participant team.implementer --actor implementer-1 --seed "$IMPLEMENTER_SEED" \
      --kind working_status --ttl-seconds 3600 --body -

That status is broadcast, wakes `wait`, records no claim, and needs no reply
or close. Use a directed `send` when a particular recipient must acknowledge
and disposition the message:

    printf '%s\n' 'Ready for review.' | "$BATON" --config "$DEMO/baton.json" send \
      --participant team.implementer --actor implementer-1 --seed "$IMPLEMENTER_SEED" \
      --to team.reviewer --kind ping --retention transient --body -

    printf '%s\n' 'Approved.' | "$BATON" --config "$DEMO/baton.json" reply "$CLAIM_ID" \
      --participant team.reviewer --actor reviewer-1 --seed "$REVIEWER_SEED" \
      --kind review --outcome approved --retention durable --body -

Substantive reviews and implementation responses should remain durable bodies
and be materialized into whatever review folder the consuming project uses
(`materialize --dir DIR --prefix P`). The file is a human-facing artifact;
short protocol acknowledgements stay inline. Where those folders live, and how
they are named, is the consuming project's policy — not Baton's.

For production use, keep the config and SQLite database in a dedicated local
instance directory outside participating project trees. Each long-lived actor
uses one stable 32-hex seed and one active consumer path.

## Minimum requirements

Requires Python 3.11 or newer, Linux, and SQLite 3.37.0 or newer on a local
filesystem. No third-party Python packages are required. Missing runtime
requirements fail closed with documented exit code 2.

## Development

The checked-in `justfile` provides the local development workflow. These
recipes require `just`, but the shipped Baton executable does not. The
repository-local `.venv` contains development tooling only; Baton remains a
stdlib-only zipapp.

- `just venv` creates `.venv` when needed and installs the pinned packages in
  `requirements-dev.txt`.
- `just test` runs the complete reusable suite in `test_baton_v6.py`.
- `just build` rebuilds the deterministic `bin/baton` zipapp and refreshes
  `DISTRIBUTION.json`.

After a fresh clone, run `just venv` once, then use `just test` for normal
verification. Test and build recipes fail with a direct instruction if the
local venv has not been bootstrapped.

## Instance

An instance is a directory holding `baton.json` (the config, always passed
explicitly via `--config`) and `mailbox.sqlite3` (the single authority; its
WAL/SHM siblings belong to SQLite). There is no other authoritative file.
Create one with:

    baton --config /abs/path/instance/baton.json init

See `example-baton.json` for the config shape: participants are dotted
addresses with `identity` `agent` (any actor) or `singleton` (one bound
actor); administrative authority is granted ONLY by an explicit
`capabilities` list (`recovery`, `config`) — never inferred from identity.
`roots` name the directories attachments may reference. `retention_days`
bounds transient-metadata garbage collection.

## Core commands

`send` (body from stdin/file XOR `--attach ROOT:REL/PATH`), `send-notice`
(finite TTL, default 86400s), `claim` (one lossless delivery: claim metadata
plus envelope with base64+sha256 body or pinned attachment tuple), `wait`
(the same directed delivery, or a broadcast notice — see below),
`reply` / `close` (effectively-once: retries redeliver the committed
disposition and mismatches fail closed), `see` / `expire` (notices),
`recover-claim` (requires the `recovery` capability and a reason),
`quarantine-attachment` (terminal disposition for a message whose pinned
attachment no longer verifies; requires `recovery` and a reason — see below),
`snapshot` (validated copy of a maintenance-gated instance; requires
`config`), `gc`, `regen` (accept a generation+1 config; requires `config`),
`scan`, `doctor`, `dump`, `inspect`, `materialize`.

`migrate` is an audited gate, not a conversion capability. It requires the
participant's `config` capability and the maintenance gate, durably audits the
attempt, and then refuses with exit 4 — this build knows one protocol and has
no path to convert an instance from another. A migration path is added only
alongside a protocol bump. To move an instance to a newer protocol, retire it intact and start a
fresh one at the target protocol: coordination comes back in minutes, and
anything still needed is re-sent. Converting in place keeps more history but
takes the channel down for the whole conversion, including for whoever would
have to review it.

## Damaged attachments

An attachment is hash-pinned when the message is published, so editing the
file afterwards invalidates the pin. `claim` and `wait` **skip** such a
message and deliver the next healthy one, rather than failing the whole queue;
naming it explicitly with `--message-id` still fails closed. Skipped damage is
listed by `scan` under `damaged` and by `doctor`.

A skipped message stays pending until dispositioned. `quarantine-attachment`
is that disposition: it records the original pin and the observed failure in a
permanent audit row and moves the message to a terminal `quarantined` state,
without ever claiming it — damaged content is never delivered, so no claim is
created. An already-terminal message is acknowledged without rewriting its
history. `doctor` then reports the damage as an acknowledged warning rather
than an unresolved problem.

The practical lesson: send a document that is still being edited as a
`--body`, which is copied into the store, and attach only what is final.

## What `wait` delivers

`wait` blocks until exactly one delivery is available on either inbound
channel and prints it as JSON. The two shapes are distinguished by key:

    {"claim": {...}, "message": {...}}   a directed message, now claimed
    {"notice": {...}}                    a broadcast notice, marked seen

A pending directed message always wins when both are available, so claimable
work is never delayed behind advisory broadcast, and a consumer that only
ever receives directed traffic sees the directed shape unchanged.

A notice is not claimed — there is nothing to `reply` to or `close`. The
`notice_seen` receipt commits in the same transaction as the read, exactly as
`see` has always done, so `wait` and `see` never deliver the same notice twice
to the same participant+actor. Each participant, and each actor of a
participant, receives its own independent copy.

That receipt is also why broadcast is **at-most-once**: a consumer that dies
after the commit but before acting on the bytes does not get the notice again.
At-least-once would require per-recipient acknowledgement — that is a claim,
and a notice has no per-recipient message row to claim. Use a directed message
for anything that must not be missed.

Projections: `materialize --dir DIR --prefix P` re-emits a durable body as a
byte-exact `P-<created>-<id>.md` file. The prefix is an EXPLICIT caller
choice; participants' configured `projection_prefix`/`projection_dir` define
which files `doctor` owns and inventories (orphans are warnings).

## Maintenance and moves

`maintenance-enter/exit` gate the instance (exit refuses during a move).
A move binds one source and one destination config path plus their directory
identities immutably at entry; `move-copy`, `move-bind`, `move-activate`,
`move-decommission`, and `abort-move` are exact-token audited ceremonies —
at most one instance with a given UUID can ever be active through the API.

## Exit codes

0 success · 2 minimum requirements unmet · 3 nothing eligible ·
4 validation/usage · 5 race/busy · 6 integrity damage ·
7 gated (maintenance/moved).

## Distribution

`just build` invokes `build_zipapp.py` to build the canonical deterministic
`bin/baton` zipapp and refresh `DISTRIBUTION.json` (tool/protocol versions,
minimum runtime versions, artifact hash). `python3 build_zipapp.py [outdir]`
remains available when building into another distribution root. Same inputs,
same bytes. A complete deployment also ships the generic
`AGENTS-MAILBOX-PROTO.md` beside the executable; consumer projects keep only
their local participant bindings and discover paths from the deployment rather
than hard-coding a checkout or host layout.
