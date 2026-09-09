# Codex copilot notifier (v11)

`codex_copilot_notifier.py` observes an operator's actionable Work, pending
obligations, open managed-turn incidents and failed runtimes through the canonical
Baton CLI. It asks the existing Codex event
bridge to notify an existing prompt thread. It does not connect to app-server
directly, start another model context, claim Work, consume handler readiness,
or change the Baton database. Due trials owed by the operator are included.

The automatic turn is **advisory only**: read evidence, summarize, recommend,
and propose commands. It must not execute prior approvals, edit files, run
tests, request escalation, or change workflow. Normal human-initiated turns
are unchanged. This is a cooperative instruction boundary, not an OS sandbox.
The bridge's managed approval-denial policy remains unchanged: missing read
permission is reported to the human, not solved through unattended prompts.

## Configure and launch

Requires Python 3 on Linux (standard library only) and the paired bridge
changes for `copilot-status` and advisory admission. Put the following JSON
in an operator-owned file; replace every example path/identity with the
deployment's actual values. The notifier config is NOT `baton.json`.

```json
{
  "baton": "/absolute/deployment/bin/baton",
  "baton_config": "/absolute/coordination/baton.json",
  "observer": "baton.slaw",
  "prompt_participant": "baton.prompt",
  "target": "baton-prompt",
  "socket": "/absolute/coordination/run/codex-events.sock",
  "state_file": "/absolute/coordination/run/codex-copilot-notifier.json",
  "poll_seconds": 30,
  "timeout_seconds": 15,
  "obligation_reminder_seconds": 600
}
```

Use an existing private writable directory for the cursor and lock. Keep one
notifier per target, using the same state path on every restart. The state-file
lock refuses a concurrent invocation on that path. Distinct state paths are
NOT a way to create multiple observers of the same prompt.

First inspect the existing live dispatcher config: the target must map to the
exact prompt participant, role `prompt`, and the thread attached to your UI.
This tool discovers that configured thread from bridge status; it never creates
or rebinds one. Do not point it at a reviewer/implementer thread. Mismatched
participant/role/thread or bridge incarnation refuses rather than redirects.

Read-only preview (no socket, cursor changes or model turn):

```bash
python3 tools/codex_copilot_notifier.py --config /absolute/notifier.json --dry-run
```

After independent review, deploy/restart the bridge through the existing
drain-aware procedure, preserving the interactive prompt mapping. Then, when
the prompt is idle, test one poll and verify the summary appears in your UI:

```bash
python3 tools/codex_copilot_notifier.py --config /absolute/notifier.json --once
```

`accepted` means the bridge accepted an advisory, not that the model has
completed its analysis. `waiting-for-prompt` and `not-accepted` do not consume
attention. Once UI delivery is confirmed, run in a dedicated foreground
terminal (Ctrl-C stops only this watcher):

```bash
python3 tools/codex_copilot_notifier.py --config /absolute/notifier.json
```

No service has been added to `infra.py`. Start/stop integration can follow
the first live proof; don't restart other agents merely to run the dry-run.

## Unresolved-obligation reminders

Pending response obligations owed by the configured operator remind again every
10 minutes by default. Set `obligation_reminder_seconds` to `300` for 5 minutes,
or `0` to disable repeat reminders. The setting accepts finite nonnegative
seconds. New or changed obligations still notify immediately when the prompt
is idle; trials, Work and failure attention retain change-based deduplication.

Each reminder poll reads current canonical obligations and handler membership.
Resolved or no-longer-owed obligations are removed. Due reminders coalesce into
one advisory, with at most 50 locators per event; later polls offer any remaining
items. An obligation's timer advances only when an event containing its locator
is accepted. Busy, disconnected or rejected delivery leaves it due, and accepted
advice about unrelated attention does not postpone it. Acceptance remains bridge
admission, not proof of model completion, UI display or an operator response.

**How the 50 are chosen, because the order is part of the contract.** New or
changed attention comes first, keeping its immediate promise. Due reminders
follow, ordered by each obligation's own anchor — its acceptance time, or the
migration anchor a legacy entry was given — oldest first, with the locator
breaking ties. Acceptance moves a record to the back of that order, so the
obligations that have waited longest lead the next eligible advisory and the
remainder genuinely arrives.

Ordering the batch by locator alone does not do this, and the difference is not
cosmetic. Change-based attention drains, because acceptance records its hash and
it stops being changed; an accepted reminder deliberately becomes eligible
again. Merging both into one alphabetical list and taking the first 50 therefore
hands the same early locators every batch indefinitely. With 60 pending
obligations and a supported 300-second reminder and poll interval, ten never
received an initial advisory — or, if all 60 had been accepted first, never
received a due reminder at all. That was W119521's review finding and it is
fixed; the ordering above is what fixes it.

Anchors move only when an offered locator is accepted, so a refused or busy
batch is retried as the same event rather than reshuffled. A batch that has
genuinely gained a longer-overdue obligation is a different batch and carries a
different identity.

The cursor now also stores each response obligation's accepted hash, acceptance
time and generation. Generations distinguish successive reminders; retries of
the same pending batch keep a stable event identity. Times are wall-clock Unix
seconds so process restarts preserve deadlines. A backward clock adjustment can
delay the next reminder; a forward adjustment can make it due on the next poll.

Existing hash-only cursors migrate without clearing seen hashes or replaying all
attention. On the first poll, each still-present legacy obligation gets a saved
migration anchor; its first repeat becomes due one configured interval later.
Its acceptance time stays unknown until a corresponding advisory is accepted.
Restart, busy polls and unrelated accepted events preserve that anchor. With
reminders disabled, saved acceptance times remain available; re-enabling may
make an older obligation immediately due. Bridge/thread scope changes retain
the existing fresh-attention behavior described below.

After review, restart only the notifier to load its updated code/config, keeping
the same cursor and prompt mapping. This change needs no bridge or stack restart;
deployment/restart remains an explicit operator action.

## Bounded delivery behavior

- Polls every 30 seconds by default; CLI/socket operations have timeouts.
- Reads all actionable-work pages. Obligations are team-wide in the CLI, so
  the watcher filters by the resolved endpoint's operator handler membership.
- Reads `incidents` and `runtime`, filtering both by exact `action_owner` equal
  to the configured observer. A stranded claim can notify even when no Work is
  offered to the operator. Incident dismissal and runtime recovery are separate:
  an open incident remains attention after the runtime recovers.
- Failure locators are `incident:N` and `runtime:TEAM.MEMBER`. The copilot reads
  those canonical views and the correlated Work before recommending recovery;
  the notifier never releases claims, dismisses incidents or inspects logs.
- Correlates participant, incarnation, session, Work, episode and cause, requiring
  the incident to begin at or after the runtime's failed transition. When both
  appear, sends the incident locator once. A later matching representation is
  silently acknowledged only if its counterpart was already accepted. Separate
  episodes/sessions and later failed transitions notify again. No claim of atomic
  snapshots or detection of transitions that disappear entirely between polls.
  A cursor marker remembers when a runtime version has already been paired with
  an incident, so a new incident after dismissal still notifies. Existing cursors
  without this optional field remain readable.
- Work handoff changes, message counts and child progress can trigger advice;
  runtime ages/heartbeats, incident occurrence counters, New cursors and pickup
  timers cannot repeatedly wake the model. Runtime `since` identifies state
  transitions, not lease refreshes. Missing correlation causes separate alerts
  rather than suppressing a potentially independent incident.
- Coalesces in the watcher while busy. The bridge also checks idle admission,
  preventing an old busy observation from accumulating another advisory.
  A human turn racing admission still uses the existing dispatcher's busy and
  ambiguous-start handling; no turn is interrupted or steered by the notifier.
- Reads again before the next send; resolved items are pruned. The model must
  re-read canonical state because notification and execution aren't atomic.
  Derived stale `unknown` from lease expiry is not recovery: retain only already
  accepted failure hashes and pairing markers through expiry, including when
  unrelated attention is delivered. Identical renewal does not notify again;
  rejected or busy deliveries remain unacknowledged. Reported recovery, absence
  or changed ownership prunes runtime memory; a changed failed version (including
  a replacement incarnation) is new attention. Stale rows themselves never alert.
- Stores hashes/locators, reminder timestamps and generations as its delivery
  cursor (0600 atomic replacement).
  This is not coordination authority. No direct SQLite access.
- Deduplication is scoped to authority, operator, prompt and bridge incarnation.
  A bridge restart or prompt thread replacement re-offers current attention.
  Reconnection to the same incarnation retains the saved cursor.
- Lost acknowledgements and crash windows can duplicate summaries. Delivery is
  not exactly-once. A failed model turn after socket acceptance is not retried
  as a failed turn: inspect it, then request a manual scan. A still-pending
  response obligation can independently become due for its next reminder.
  No automated recovery.
- An advisory without enough read permission reports the command needed. It
  does not obtain permission or act on your behalf.

## Focused verification

From repository root:

```bash
python3 -m unittest tools.test_codex_copilot_notifier -v
node --test tools/codex-event-bridge/test/event_types.test.mjs tools/codex-event-bridge/test/event_bridge.test.mjs
```

Tests use fake CLI/protocol responses and a local temporary Unix socket, not
live agents, credentials, containers or provider APIs. A restricted sandbox
may need explicit permission for the socket fixture. No broad suite is needed.

Decision/evidence: [notifier dossier](../work/records/2026/09/finding-v11-codex-copilot-notifier/FINDING.md).

Failure detection extension: [W114322](../work/records/2026/09/finding-v11-copilot-run-failure-notifications/FINDING.md).
After independent review, restart only the existing notifier process to load this
change, keeping its config and cursor. No bridge or stack restart is required.
The first poll offers existing unresolved incidents/failures as well as new ones.

Reminder decision/evidence: [W119521](../work/records/2026/09/finding-copilot-reply-visibility/FINDING.md).
