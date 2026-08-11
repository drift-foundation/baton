# Using Baton effectively

This is the short operating guide for teams coordinating humans and AI agents
with Baton 1.0.0. The [README](../README.md) is the complete command and
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
administrator with the `config` capability writes the new config at the same
path with `generation` incremented by exactly one, then runs
`regen --participant <admin>`; Baton accepts or refuses it in one transaction.
Editing the file alone changes nothing, and the SQLite database is never
edited by hand.

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

### Codex live-turn polling observed here

A terminal process can remain in the background, but its completion does not
by itself schedule another Codex turn. If the model returns control while
`wait` is still running, a later readiness result may sit unread until the user
or runner starts a new turn.

While assigned to monitor Baton, keep the Codex turn alive and poll the actual
terminal session at a bounded interval, such as 60 seconds. A process merely
appearing in a process list is not enough: inspect its output, because a wait
loop exits as soon as it reports readiness. Claim or `see` inside that same
live turn, resolve any claim, and re-arm. A detached/background process may
detect work, but it must never perform the claim.

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
