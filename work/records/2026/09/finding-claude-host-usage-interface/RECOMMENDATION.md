# Claude usage collection recommendation — 2026-09-25

Investigation only; no proposed command below was executed. No product change
or implementation authority is implied. Owner live /usage observations remain
historical evidence, not an author measurement.

## Conclusion

**Confirmed:** Claude has noninteractive usage surfaces. The checker currently
collects neither. Do not describe the ACP-configured account as lacking data.
**Recommended small change, subject to owner selection:** consume supported
`rate_limit_event` fields from the existing Claude live probe's JSON stream.
This adds no second model request or direct account HTTP endpoint. It supplies
only windows actually reported; it cannot promise a complete session/week
snapshot every invocation. Preserve unavailable output for missing fields.

For a complete human view today, use interactive `/usage` in the selected
account. The installed version also implements a native noninteractive `/usage`
report. Do not parse that text into percentages or blindly relay its entire
output in the aggregate checker: it can include local activity attribution.

No stable, complete, on-demand structured snapshot interface was established.
A structured `get_usage` control request exists in this installed binary but
is explicitly experimental. Its existence is evidence of capability, not a
supported contract on which to base this bounded patch.

## Evidence and support levels

Installed executable resolves to `/home/sl/.local/share/claude/versions/2.1.263`,
215662064 bytes, SHA-256
`26d020351e8112f4006790f3cfce43b4c9df0c1bb1d0e542364d64151b81d5ba`.
Read `claude --help` only; inspected embedded shipped JavaScript read-only.
These byte offsets locate evidence in that exact binary; they are not runtime
API names to import or entry points to invoke:

- 186370533: usage command table defines both interactive local-jsx and local
  noninteractive implementations; local entry enables supportsNonInteractive
  and loads chunk-1x6nec5z.js. At 177078314, its noninteractive predicate reads
  the launch option. This is stronger evidence than assuming -p cannot /usage.
- 192898073 onward: native report formats session/all-model weekly utilization
  and resets, optionally model-specific buckets. It floors percentages for text
  display. Nearby handler calls the provider-owned usage function and can include
  behavioral analysis of local transcripts. It returns text, not stable quota JSON.
- 178912838: rate-limit event schema; 184685591: formatter; 199303769:
  stream-event producer. Top-level fields describe the currently limiting window.
  The additional `unifiedWindows` map is explicitly internal in this build;
  do not silently treat it as a public promise of both windows.
- 179036623: experimental get_usage schema with skip_behaviors; 192888148:
  aggregate implementation; 199618802: control dispatch; 197458183: SDK wrapper
  whose name explicitly says EXPERIMENTAL_MAY_CHANGE_DO_NOT_RELY_ON_THIS_API_YET.
  skip_behaviors avoids the local seven-day transcript scan. No such call was made.

Official references retrieved 2026-09-25:

- [CLI reference](https://code.claude.com/docs/en/cli-reference): print mode
  supports JSON streaming and verbose output. Installed help agrees. Use a
  subprocess under existing bounds; no SDK dependency is needed.
- [SDK commands](https://code.claude.com/docs/en/agent-sdk/skills#commands-in-agent-sdk-sessions):
  noninteractive commands are discoverable in init.slash_commands; the example
  includes usage. Commands are sent as prompts. Unknown commands on newer
  versions can fall through to a model turn, so arbitrary version fallback is
  not a safe no-model guarantee.
- [Command reference](https://code.claude.com/docs/en/commands): /usage includes
  plan limits as well as cost/activity. These are distinct quantities.
- [Official Python SDK types](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py),
  RateLimitInfo/RateLimitEvent around lines1270–1305: optional utilization is a
  fraction, reset is epoch seconds, type identifies the window; events report
  rate-limit changes, not guaranteed full snapshots.
- [Official SDK parser](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/_internal/message_parser.py),
  lines341–356: wire event uses rate_limit_info with camelCase resetsAt and
  rateLimitType. This supports the exact shape below; do not confuse it with
  the Python object's snake_case attributes.
- [Status-line reference](https://code.claude.com/docs/en/statusline): script
  input contains five-hour/seven-day percentages and epoch resets. This is an
  interactive display callback, not evidence it runs in print mode. Installing
  a status-line collector would change user configuration and need a separate
  lifecycle/freshness design; it is not the recommended patch.

Operational limitation: the TypeScript reference could not be fetched (web tool
reported content over4MiB; markdown fallback failed). It is not cited as read.
The official Python source plus installed CLI cover the proposed wire fields.
No credential file, account configuration contents, or transcript was read.

## Exact proposed interface and output shape

Preserve selected-home child_environment and temporary working directory from
`tools/provider_checks.py`. Change only the existing Claude live argv's format
from json to stream-json and add --verbose:

```sh
claude --print --output-format stream-json --verbose --no-session-persistence \
  --tools '' --disable-slash-commands --setting-sources '' \
  --settings '{"disableAllHooks":true}' --strict-mcp-config \
  --mcp-config '{"mcpServers":{}}' -- \
  'Reply with pong. Do not use tools, inspect files, or perform any other action.'
```

This is a future host-check command, not an investigation instruction to run it.
Set CLAUDE_CONFIG_DIR to the inventory's selected absolute home; remove the same
credential/backend overrides as today's child_environment. Never use --bare:
installed help says it bypasses OAuth/keychain and changes authentication.

Illustrative wire shape, not a captured response:

```json
{"type":"rate_limit_event","rate_limit_info":{"status":"allowed","rateLimitType":"five_hour","utilization":0.13,"resetsAt":2000000000},"uuid":"example","session_id":"example"}
```

Proposed parser: preserve the terminal result event as the live verdict; quota
is informational. Accept only exact five_hour and seven_day for aggregate
session/week. Validate finite numeric non-boolean utilization in [0,1], convert
remaining as 100*(1-utilization), validate epoch reset separately, mark expired
snapshots unavailable. Reject out-of-range/unknown fields rather than inventing
values. Other model/overage buckets are not total weekly allowance. No event or
missing field is unavailable, never 100%. Track only events from this subprocess
and consistent session identity; contradictory/ambiguous windows fail closed.
Only bounded sanitized renderings escape the helper, never verbose stream text.

Implementation size: adapt Claude live result decoding to bounded NDJSON,
retain applicable quota events in the same check result, reuse compact renderer;
no extra process, SDK or persistent cache. Deterministic tests: interleaved
messages, result present/missing/failure, absent quota, each window, null/invalid/
boolean/out-of-range fields, stale resets, wrong session, model/overage rejection,
output cap/timeout/interrupt and unchanged per-home selection. Owner live
confirmation only after independent review, if selected. No tests ran here.

## Native report and experimental snapshot alternatives

Manual fallback in the already-open selected account: enter `/usage`.
To launch that account explicitly, set `CLAUDE_CONFIG_DIR` to its existing home
in a clean operator environment, launch `claude`, then enter `/usage`. Clear
ambient API-key/OAuth-token/alternate-backend overrides as the checker does;
CLI/keychain semantics still own the account identity.

Source-supported noninteractive native-report candidate, not executed:

```sh
claude --print --output-format json --no-session-persistence \
  --tools '' --disable-slash-commands --setting-sources '' \
  --settings '{"disableAllHooks":true}' --strict-mcp-config \
  --mcp-config '{"mcpServers":{}}' -- '/usage'
```

Use the same selected-home clean environment and private cwd. Expected result is
CLI local-command text in the JSON result envelope, with native used percentages
and resets when available, plus possible subscription/activity sections. It is
not a structured allowance object. Local source establishes command support,
not a live guarantee for these flags/account. Before any automated native-report
adapter, independently confirm dispatch cannot fall through to model output and
bound/control the local transcript scan; otherwise use the manual interactive
report. Rendering untrusted arbitrary stdout or parsing changing report lines
is not recommended.

Experimental snapshot's exact request payload is
`{"subtype":"get_usage","skip_behaviors":true}` within the CLI control protocol.
Its response contains session cost, subscription_type, rate_limits_available,
nullable rate_limits and behaviors. five_hour/seven_day windows use utilization
in percent (0–100) and string resets_at, unlike stream-event fractions and epoch
seconds. No supported stable wrapper was established. Do not build a raw-control
client or call its underlying account endpoint as a workaround. If owner requires
both windows on demand with zero model request, this stability gap remains the
explicit limitation; manual /usage is the available fallback.
