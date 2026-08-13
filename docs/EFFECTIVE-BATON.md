# Using Baton effectively

This is the short operating guide for teams coordinating humans and AI agents
with Baton over protocol 10. It is written against the protocol rather than
against a product version: `baton` and `baton-tui` are independently versioned
products, so "Baton 1.0.0" no longer names one thing, while the protocol is
what actually decides whether two participants can work together.
The [README](../README.md) is the complete command and
storage contract. [AGENTS-MAILBOX-PROTO.md](AGENTS-MAILBOX-PROTO.md) is the
protocol-10 agent-channel contract and convention reference. A participating
repository's own `AGENTS.md` binds its roles and workflow to concrete
participant addresses.

## Onboard a team

The local deployment supplies two absolute paths:

    BATON_BIN=/absolute/path/to/bin/baton
    BATON_CONFIG=/absolute/path/to/mailbox/baton.json

Do not infer either path from the current repository. The config and SQLite
authority live outside participating product trees.

Give each role one scoped participant address, such as `payments.implementer`
or `payments.reviewer`, and record that mapping in the product's agent policy.
The participant address is the identity; protocol 10 has no actor or seed.

Before joining normal work, verify the released executable and authority:

    "$BATON_BIN" --version
    "$BATON_BIN" --config "$BATON_CONFIG" doctor

Config changes take effect only through the audited `regen` ceremony. An
administrator writes the proposed config at the same explicit path with
`generation` exactly one greater than the authority's accepted generation,
then a participant with the `config` capability runs
`regen --participant <admin>`; Baton accepts or refuses the proposal in one
transaction. Writing the proposal changes no authority state, but ordinary
operations refuse while the file's generation or digest differs from the
accepted state. If `regen` refuses, the authority remains unchanged: correct
and retry the still-generation+1 proposal or restore the exact accepted JSON
before resuming ordinary work. Never edit the SQLite authority directly or
treat an unaccepted config file as active state.

## Keep one active receive loop

While a participant is active, keep exactly one readiness path armed:

    "$BATON_BIN" --config "$BATON_CONFIG" wait \
      --participant payments.reviewer --timeout 60

`wait` is read-only. It claims no message and marks no notice seen. A timeout
exit is idle, not failure; re-run it. A successful result must be consumed in
the same live turn:

- For `"channel": "message"`, claim the exact reported id:

      "$BATON_BIN" --config "$BATON_CONFIG" claim \
        --participant payments.reviewer --message-id MESSAGE_ID

- For `"channel": "notice"`, receive notices atomically:

      "$BATON_BIN" --config "$BATON_CONFIG" see \
        --participant payments.reviewer

  `see` has no id: it marks every unseen notice for the participant seen and
  returns them together.

Resolve every claim immediately with `reply` or `close`. Never end a turn
holding a claim, and never run two claimers under one participant identity.
After resolution, re-arm `wait`.

## Run the loop under your agent runner

Baton defines readiness and consumption; it does not schedule model turns.
Whether a background process can wake an agent, how long a command stays in
the foreground, and how monitor events enter a conversation are runner
behavior. Keep that behavior in local operating policy, not in the portable
protocol.

Every runner shares two rules: one active consumer path per participant, and
no turn ends with an unanswered claim. A monitor is read-only and advisory; it
must never claim, mark a notice seen, reply, or close on the model's behalf.

### Claude Code monitor pattern observed here

Long foreground waits may be detached when the turn ends. A detached protocol-
10 `wait` is safe because it is read-only, but readiness can then sit with no
live turn to consume it. Use waits short enough to remain inside the turn and
treat idle exit 3 as "run it again." A separate runner monitor may wake or
interrupt the agent when read-only mailbox state changes, if that runner
supports such events.

Monitor notifications can lag or repeat. Re-derive the current truth with
`wait` or `scan`; never treat a notification as a consume step. If monitor
events enter the same conversation channel as human input, they are not human
instructions, approvals, or decisions.

Assume a conversation can be compacted or restarted between checks. Decisions,
evidence, rejected approaches, and current progress belong in Baton content
and the finding folder, not only in the transcript.

### Codex app-server event pattern

Codex uses its app-server integration rather than relying on completion of a
background terminal command to schedule another model turn. Claude Code keeps
the runner-specific monitor pattern above; do not substitute the Codex
app-server mechanism for Claude's own event integration.

Create one machine-level bridge configuration that lists every Codex-backed
participant, its target, and its persistent thread ID. It also records the
deployment's explicit Baton executable and config paths. There is exactly one
supervisor for that configuration: individual repositories and Codex sessions
do not start their own bridge or Baton poller. Start the complete foreground
stack once from the Baton repository:

    just codex-baton /absolute/path/to/codex-event-bridge.json

That single recipe starts every configured loopback app-server, waits for
readiness, starts one shared multi-target bridge, requires successful initial
resume of every configured thread, then starts one read-only Baton monitor for
every configured participant and target. Duplicate participant assignments are
refused. If any component exits, the supervisor stops the rest and exits
visibly; Ctrl-C also stops the complete stack.

For example, two independent reviewer sessions use two independent mappings:

```text
baton.reviewer -> target baton-reviewer -> thread T-baton
lang.reviewer  -> target lang-reviewer  -> thread T-lang
```

The supervisor runs one `wait --participant baton.reviewer` child and one
`wait --participant lang.reviewer` child. Readiness from the first starts a
turn only on `T-baton`; readiness from the second starts a turn only on
`T-lang`. The sessions share app-server infrastructure, but not identity,
conversation context, queue, busy state, or mailbox head.

The low-level `just codex-app-server` recipe starts only the backend and is for
protocol development. It does not wire Baton. Do not expose the experimental
app-server WebSocket on `0.0.0.0` or a public interface.

Connect each normal Codex TUI to that backend:

    codex resume --remote ws://127.0.0.1:4500 THREAD_ID

Before the first shared launch, close any Codex TUI still running the configured
thread through its old per-session backend. Codex permits only one active
writer for a persistent thread. If a target still has an active writer, the
supervisor names that unavailable target, starts no Baton monitors, and stops
the partial stack. Start the shared stack first, then resume each TUI through
the displayed remote endpoint.

The normal startup order is therefore:

1. Close old isolated Codex sessions that own configured threads.
2. Start the one machine-level `just codex-baton SHARED_CONFIG` supervisor and
   wait for its `ready` line.
3. For each desired reviewer TUI, run `codex resume --remote ENDPOINT THREAD_ID`.
4. Leave the supervisor running. TUIs may disconnect and reconnect without
   stopping their participant's Baton monitor.

Do not fall back to `codex resume THREAD_ID` after migration. Without
`--remote`, Codex starts an isolated backend, takes the thread's writer lock,
and prevents the shared bridge from resuming that target.

Each logical agent owns one established persistent Codex thread. Its TUI and
the event bridge are peer app-server clients operating on that thread ID. The
bridge can manage many target/thread pairs concurrently; one busy agent does
not block another. Configure those mappings as described in
[CODEX-APP-SERVER-EVENT-CONNECTIVITY.md](CODEX-APP-SERVER-EVENT-CONNECTIVITY.md).

Each supervised monitor is its participant's one active Baton readiness path.
Do not run a second manual or background `wait` for the same participant. The monitor never
claims a message, marks a notice seen, replies, or closes. It forwards only a
readiness event through the local Unix socket:

- a message event carries the exact `message_id` reported by `wait`;
- a notice event reports that a batch is ready for `see`;
- repeated readiness for the same unresolved head is suppressed;
- if the bridge is unavailable, the monitor retains responsibility and retries.

The app-server injects that event as a new turn in the configured agent thread.
The event is external input, not a human instruction or approval. The awakened
Codex agent follows the repository's standing policy: claim the exact message
ID from the event, or call `see` for notices, process the content, resolve every
claim with `reply` or `close`, and return. It does not invoke `wait`; the monitor
already owns and re-arms that readiness path.

This replaces the earlier Codex live-turn polling workaround, whose terminal
completion could not itself schedule another turn. The old workaround remains
useful only when Codex is not running through app-server.

Other runners may offer stronger wakeup primitives. Record what the deployment
actually observes rather than copying Claude- or Codex-specific ergonomics
into an environment with different scheduling behavior.

## Make the inbox useful

Give substantive work a concise subject. When one line is the whole message,
use `--tweet`; it publishes the line as the subject with no body:

    "$BATON_BIN" --config "$BATON_CONFIG" send \
      --participant payments.implementer --to payments.reviewer \
      --kind status --tweet "Still testing; give me more time"

Use a directed message when somebody owes an answer or acknowledgement. Use a
finite-TTL notice for information that nobody claims. Scope a team notice with
a quoted selector such as `--scope 'payments.*'`; quote it so the shell cannot
expand it.

When a message discusses repository files, include a references part. The
references file contains one configured `ROOT_ID:relative/path` per line:

    "$BATON_BIN" --config "$BATON_CONFIG" send \
      --participant payments.implementer --to payments.reviewer \
      --kind implementation_handoff \
      --subject "Retry finding ready for review" \
      --body work/finding-retry/PROGRESS.md \
      --references /tmp/retry-handoff.references

References are navigation, not copied evidence. The body is copied into the
authority. Use an external attachment only when you deliberately mean to pin
an immutable file hash; do not attach a document that is still being edited.

For a short acknowledgement, reply with `--tweet`. For a substantive review,
reply with a nonempty body and references. If no response content is needed,
`close` records the terminal disposition.

## Preserve work in findings

Baton messages are durable coordination evidence, but they should not be the
only specification of a product or engineering decision. A recommended team
workflow is one folder per independently schedulable item:

    work/finding-short-slug/
      FINDING.md
      PLAN.md
      PROGRESS.md
      review-YYYY-MM-DDTHH-MM-SSZ.md

This layout is team policy, not protocol enforcement. A repository may adapt
the names, but the responsibilities should remain distinct:

- `FINDING.md` records observed behavior, evidence, confirmed decisions,
  boundaries, and acceptance criteria.
- `PLAN.md` says what is currently actionable and in what order.
- `PROGRESS.md` is the implementer's account of what was actually changed,
  rejected, tested, and learned.
- Append-only review journals preserve each review outcome and correction
  round instead of rewriting history.

Before implementation, pin every confirmed product, UX, protocol, or
operational ruling in the owning finding and update the plan. Label hypotheses
as hypotheses; a reviewer or implementer message is evidence to verify, not
authority. When work resumes after a crash or context reset, read the whole
finding folder and revalidate it against the current tree.

Handoffs should carry the explanation as a body and list every discussed file
in a references part. That tells the reader which exact finding, plan,
progress, review, source, and test files matter even when several unstaged
changes coexist.

Implement one finding serially to a reviewed terminal state. Reviewer research
may enrich queued findings without interrupting the implementer. After the
resolution is committed, clean up ephemeral finding folders deliberately;
durable tests, user documentation, and repository policy must stand on their
own before the folder disappears.

## Recover content and diagnose safely

`claim` and `see` print lossless typed content. To recover a durable part later,
use the authorized public projection command:

    "$BATON_BIN" --config "$BATON_CONFIG" materialize \
      --participant payments.reviewer --dir /absolute/projection/directory \
      --prefix review --part 0 MESSAGE_ID

The projection is a cache; the authority remains canonical.

Use `scan` for pending/claimed/damaged inventory and `doctor` for authority
health. Do not query or repair SQLite directly. If Baton cannot express a
needed recovery or diagnosis, file a Baton finding rather than inventing a
private database workaround.

## Keep released communication stable during development

Normal users should continue invoking the canonical released `bin/baton` and
`bin/baton-tui` against the live authority. Source work does not change those
self-contained zipapps until they are rebuilt.

During Baton development:

- build candidate zipapps into a separate development distribution path;
- test them against a separate development config and authority;
- never migrate, regenerate, gate, or replace the live mailbox as a side
  effect of feature work;
- replace canonical artifacts or cut over protocol only after focused review,
  human trial where applicable, the complete suite, deterministic rebuild,
  packaged workflow smoke, live health check, and an announced release window.

Communication stays available first. Historical messages can be ported later
when a protocol cutover requires a fresh authority; do not keep every team
offline while perfecting a migration.

## A reliable handoff checklist

Before sending:

1. Pin confirmed decisions in the finding and update its plan.
2. Revalidate the current source instead of trusting the original hypothesis.
3. Run focused tests and record failures as well as successes.
4. Give the message a useful subject and include exact repository references.
5. Keep living documents in the body; attach only intentionally immutable
   evidence.

Before finishing a turn:

1. Resolve every claim with `reply` or `close`.
2. Record current implementation/review state in repository files.
3. Re-arm exactly one `wait` for the participant.
