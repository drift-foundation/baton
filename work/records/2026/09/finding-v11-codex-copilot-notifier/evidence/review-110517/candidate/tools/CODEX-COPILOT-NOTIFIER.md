# Codex copilot notifier (v11)

`codex_copilot_notifier.py` observes an operator's actionable Work and pending
obligations through the canonical Baton CLI. It asks the existing Codex event
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
- Work handoff changes, message counts and child progress can trigger advice;
  runtime ages, New cursors and pickup timers cannot repeatedly wake the model.
- Coalesces in the watcher while busy. The bridge also checks idle admission,
  preventing an old busy observation from accumulating another advisory.
  A human turn racing admission still uses the existing dispatcher's busy and
  ambiguous-start handling; no turn is interrupted or steered by the notifier.
- Reads again before the next send; resolved items are pruned. The model must
  re-read canonical state because notification and execution aren't atomic.
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
