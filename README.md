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

    printf '%s\n' '# Handoff' 'The implementation is ready for review.' > "$DEMO/handoff.md"
    "$BATON" --config "$DEMO/baton.json" send \
      --participant team.implementer \
      --to team.reviewer --kind implementation_handoff --retention durable \
      --subject "Payment retry logic ready for review" \
      --body "$DEMO/handoff.md"

The reviewer waits for work. `wait` prints the claimed message and its
`claim_id` as JSON:

    "$BATON" --config "$DEMO/baton.json" wait \
      --participant team.reviewer

After reviewing, copy that `claim_id` into the reply command:

    CLAIM_ID="paste-claim-id-here"
    printf '%s\n' '# Review' 'Approved.' > "$DEMO/review.md"
    "$BATON" --config "$DEMO/baton.json" reply "$CLAIM_ID" \
      --participant team.reviewer \
      --kind review --outcome approved --retention durable \
      --body "$DEMO/review.md"

The implementer receives the response with the same participant identity used
to send the handoff:

    "$BATON" --config "$DEMO/baton.json" wait \
      --participant team.implementer

### Quick inline messages

Short ACKs, pings, and decisions do not need temporary files. Pass `--body -`
and pipe the bytes on standard input (`send` and `reply` also default their
body to stdin):

    printf '%s\n' "I'm still working and testing; give me more time." | \
      "$BATON" --config "$DEMO/baton.json" send-notice \
      --participant team.implementer \
      --kind working_status --ttl-seconds 3600 --body -

That status is broadcast, wakes `wait`, records no claim, and needs no reply
or close. Use a directed `send` when a particular recipient must acknowledge
and disposition the message:

    printf '%s\n' 'Ready for review.' | "$BATON" --config "$DEMO/baton.json" send \
      --participant team.implementer \
      --to team.reviewer --kind ping --retention transient --body -

    printf '%s\n' 'Approved.' | "$BATON" --config "$DEMO/baton.json" reply "$CLAIM_ID" \
      --participant team.reviewer \
      --kind review --outcome approved --retention durable --body -

Substantive reviews and implementation responses should remain durable bodies
and be materialized into whatever review folder the consuming project uses
(`materialize --dir DIR --prefix P`). The file is a human-facing artifact;
short protocol acknowledgements stay inline. Where those folders live, and how
they are named, is the consuming project's policy — not Baton's.

For production use, keep the config and SQLite database in a dedicated local
instance directory outside participating project trees. Each participant
runs exactly one active consumer path; two consumers need two participant
addresses, not one shared identity.

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
addresses, and the address is the whole identity — there is no actor and no
seed. Administrative authority is granted ONLY by an explicit
`capabilities` list (`recovery`, `config`) — never inferred from identity.
`roots` name the directories attachments may reference. `retention_days`
bounds transient-metadata garbage collection.

## Core commands

`send` (body from stdin/file and/or `--attach ROOT:REL/PATH`), `send-notice`
(finite TTL, default 86400s), `claim` (one lossless delivery: claim metadata
plus the typed content envelope), `wait`
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

## Damaged external parts

An external part is hash-pinned when the message is published, so editing the
file afterwards invalidates the pin. `claim` and `wait` **skip** such a
message and deliver the next healthy one, rather than failing the whole queue;
naming it explicitly with `--message-id` still fails closed. A message is
damaged if ANY of its external parts is: delivering the healthy parts alone
would deliver an incomplete statement. Skipped damage is listed by `scan`
under `damaged`, per part, and by `doctor`.

A skipped message stays pending until dispositioned. `quarantine-attachment`
is that disposition: it records the damaged part — by id and manifest address —
along with its original pin and the observed failure, in a permanent audit row and moves the message to a terminal `quarantined` state,
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
to the same participant. Each participant receives its own independent copy;
there is one receipt per participant, because the participant address is the
whole identity.

That receipt is also why broadcast is **at-most-once**: a consumer that dies
after the commit but before acting on the bytes does not get the notice again.
At-least-once would require per-recipient acknowledgement — that is a claim,
and a notice has no per-recipient message row to claim. Use a directed message
for anything that must not be missed.

Projections: `materialize --dir DIR --prefix P [--part N]` re-emits one
durable content part as a byte-exact `P-<created>-<id>.md` file. The suffix
follows the part's declared media type; part `0` keeps the unsuffixed name and
any other part appends `-part<address>`. The prefix is an EXPLICIT caller
choice; participants' configured `projection_prefix`/`projection_dir` define
which files `doctor` owns and inventories (orphans are warnings).

## Subject

`--subject` is a one-line human summary — what an inbox shows before anything
is opened. It is immutable, carried losslessly to delivery, and listed by
`scan`, so a consumer can triage without fetching bodies.

It is optional: status and machine traffic can fall back to `kind`. When
supplied it must be a single line of plain text with no leading or trailing
whitespace, no control characters, and at most 255 bytes as UTF-8. Invalid
subjects are **rejected, not sanitized** — a newline in a subject is a
display-injection hazard for anything rendering an inbox, and silently
stripping it would leave the sender believing they sent something they did not.

`reply` inherits the subject it is answering unless given its own, so a thread
reads as one conversation. Retries compare the EFFECTIVE subject: an inherited
retry matches an inherited commit, and an explicit change fails closed.

## Content: typed and multipart-capable

Every body travels as an ordered collection of typed parts, even when there is
exactly one. A delivery carries `content`, not a bare body:

    "content": {
      "content_type": "multipart/mixed",
      "manifest_sha256": "...",
      "parts": [
        {"content_type": "text/markdown; charset=utf-8",
         "disposition": "inline", "filename": null,
         "size": 17, "sha256": "...",
         "encoding": "text", "text": "# Handoff\nReady.\n"}
      ]
    }

`content_type` is an IANA media type with parameters (RFC 2045);
`disposition` is `inline` or `attachment` with an optional `filename`
(RFC 2183). Markdown's `charset` parameter is required by RFC 7763, and Baton
requires it for every `text/*` type.

An **inline** leaf carries EXACTLY ONE delivery representation, named by
`encoding`: `text` for `text/...; charset=utf-8`, `base64` for everything
else. Never both. The choice follows the DECLARED type, not whether the bytes
happen to decode, so a consumer dispatches on one stable key.

`encoding` is `null`, with neither content key present, in two cases: an
**external** leaf, which carries an `attachment` pin instead of bytes, and an
inline leaf whose transient body has been scrubbed — the manifest outlives the
payload. `storage` distinguishes them.

Baton TRANSPORTS content and never renders it. No HTML, no Markdown, no
transcoding: rendering is a consumer concern, and a transport that renders is a
transport with an injection surface. `filename` is advisory metadata that
Baton never uses to open, create, or name a file; it is validated at
publication anyway, because a consumer downstream may be less careful.

### Inline and external parts

A leaf's bytes are stored **inline** (copied into the store) or **externally**
(`--attach ROOT:REL/PATH`, hash-pinned in a configured root and verified at
claim time). Both are ordinary parts: same media type, disposition, filename,
ordering, size and hash contract, and both are covered by the manifest, so
retry identity is one mechanism rather than two. A delivered leaf states which
through `storage`; an external leaf carries an `attachment` pin and no bytes,
because pointing at the file is the entire reason it lives outside the store.

A message may carry **any mix** of inline and external parts, in any order —
an explanation beside its evidence in one message, or several attachments.
Earlier protocols allowed exactly one attachment and made it mutually
exclusive with content, which forced one statement to be split across two
messages that could interleave on the queue.

An external part whose type the caller does not declare gets
`application/octet-stream` — the RFC 2046 unknown-bytes type, not a guess
sniffed from the file extension.

**External parts are permitted only on directed messages.** A pinned file can
go stale after publication, and only a directed message has the lifecycle to
notice and resolve that: claim-time verification, skip-and-continue, the
audited quarantine ceremony, and `doctor`. A notice has no claim to skip or
quarantine and commits its seen receipt inside the read transaction; a close
disposition is never delivered. Both refuse an external part at publication
rather than publish a pin that nothing verifies.

Parts are their own rows with explicit ordering, so containers nest —
`multipart/alternative` inside `multipart/mixed`, and deeper — without a schema
change. Undeclared content defaults to `text/markdown; charset=utf-8`; bytes
that contradict a declared charset are refused at publication rather than
delivered under a label that misdescribes them.

The CLI publishes at most one inline part plus one external part per message
(`--body`, `--attach`, typed by `--content-type`, `--disposition`,
`--filename`); the storage layer and the delivery envelope carry arbitrary
multipart trees, so richer CLI authoring is a capability extension rather than
another protocol change. Readers must not assume any writer restriction.

Retry identity is the complete ordered part manifest, metadata included. Two
retries that differ in part order, media type, disposition, or filename are
different operations even when every byte matches, and fail closed as
mismatches.

Directed messages and notices use the same content representation.

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
