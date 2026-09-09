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
  "timeout_seconds": 15
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
- Stores only hashes/locators as its delivery cursor (0600 atomic replacement).
  This is not coordination authority. No direct SQLite access.
- Deduplication is scoped to authority, operator, prompt and bridge incarnation.
  A bridge restart or prompt thread replacement re-offers current attention.
  Reconnection to the same incarnation retains the saved cursor.
- Lost acknowledgements and crash windows can duplicate summaries. Delivery is
  not exactly-once. A failed model turn after socket acceptance is not retried
  automatically: inspect it, then request a manual scan. No automated recovery.
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
