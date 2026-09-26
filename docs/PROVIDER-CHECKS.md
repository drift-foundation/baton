# Provider account checks

`just provider-checks` checks saved login status and makes one small live request
for every configured Codex and Claude account, sequentially. Each account gets
separate `login` and `live` results plus informational allowance lines. Invoking this task selects live provider
requests, which can consume usage; it does not log in or repair authentication.

Requires Linux/POSIX, Python 3, `just`, and the provider CLIs on PATH. The helper
uses current CLI flags; unsupported versions report failure/inconclusive rather
than falling back to a different execution mode.

## Setup

Create a private user-local configuration directory:

```sh
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/baton"
```

Save a JSON document as
`${XDG_CONFIG_HOME:-$HOME/.config}/baton/provider-checks.json`. For example:

```json
{
  "accounts": [
    {"provider": "codex", "label": "codex-default"},
    {"provider": "claude", "label": "claude-default"}
  ]
}
```

Add an entry for each additional account using a unique label and `home` naming
its existing provider configuration directory. `home` accepts an absolute path
or `~/...`; spaces are supported. It is a literal path, not shell code. Do not
put credentials in this file or commit your private inventory. No directories
are scanned for accounts and no credential files are read by this helper.

Omitted homes mean `$HOME/.codex` and `$HOME/.claude`. They **do not** inherit
`CODEX_HOME` or `CLAUDE_CONFIG_DIR` from the invoking agent. Explicit directories
must already exist; a missing directory fails both checks without CLI execution.
The selected directory is passed to the provider CLI, which owns credential
lookup, including any OS credential store. These checks report CLI availability
for that configured home; they do not independently attest a person's identity
or prove that two homes map to different remote accounts.

Run all configured accounts with one task:

```sh
just provider-checks
```

Or use an explicit private configuration path:

```sh
just provider-checks "$HOME/provider accounts.json"
```

The helper also supports a path override and a per-check timeout directly:

```sh
python3 tools/provider_checks.py --config "$HOME/provider accounts.json" --timeout 30
```

Direct helper invocation accepts `PROVIDER_CHECKS_CONFIG` when `--config` is
absent; the just task's optional positional parameter supplies that variable.
Missing, empty or malformed configuration fails before any CLI starts, with a
setup pointer. No private configuration is installed automatically.

## Results and limits

Example presentation (illustrative, not a measured account result):

```text
[codex/codex-default]
  login: ok; live: usage-limited
  Weekly: 48% remaining; resets 2026-09-28 15:30:00 UTC
[claude/claude-default]
  login: ok; live: ok
2 accounts, 4 checks, 1 failed/inconclusive
Report completed: 2026-09-25 13:40:02 UTC
```

A saved login can pass while a live request fails. Both checks run for each
account even after an earlier failure. `usage-limited` distinguishes recognized
quota/rate-limit diagnostics from recognized `authentication-error` or
`not-logged-in`. Recognized local argument/settings/MCP errors are `invocation-error` with a
fixed setup hint. Unknown failures include the CLI exit code and a pointer to
these instructions; ambiguous or
unrecognized successful output is `inconclusive`. These diagnostic categories
are best-effort, not account-level billing or credential validity guarantees.
Raw output, account emails, tokens and response text are never printed.

For `invocation-error`, compare the installed provider's `--help` with the
probe options in `tools/provider_checks.py`; check the CLI version before
changing account authentication. The Claude probe explicitly separates its
positional prompt from variadic options with `--`. An unclassified failure is
not evidence of invalid credentials: preserve the account label, check phase,
exit code and CLI version for investigation rather than sharing raw auth output.
After the reviewed correction, the owner's live-confirmation command is
`just provider-checks` (or the same optional private config path used before).
No author/reviewer live result is claimed.

Live success requires the CLI's structured successful terminal result and a
nonempty assistant response. It does not depend on model branding or exact
one-word formatting. Codex uses JSON events; Claude uses JSON stream events and its terminal result.
Exit codes: 0 means every login/live check passed, 1 means at least one failed/inconclusive,
2 means invalid/unavailable configuration or arguments, 130 means interrupted.

Each check has a 45-second wall-time bound by default (maximum configurable
300 seconds) and a 1 MiB combined capture limit. Cleanup terminates its POSIX
process group, allowing up to 0.5 seconds before SIGKILL and waiting for the
leader. Ctrl-C and SIGTERM stop the current check; later accounts are not run
on interruption. This bounds local processes in that group, not remote request
cancellation or descendants that deliberately escape the group.

Requests run in an empty temporary directory. The Codex live probe uses read-only sandboxing,
ephemeral sessions and ignores user execution config/rules; Claude disables
tools, hooks, MCP sources, skills and session persistence for this check.
Neither tests a project's full agent configuration. CLI-managed authentication
may perform its normal refresh or write its own metadata during a human-selected
live request; the helper never invokes login, logout or a refresh command.

Known credential, endpoint and alternate-backend environment overrides are
removed from **child** environments so an inherited API key does not silently
replace a selected saved login; parent environment is unchanged. This task
checks saved-login accounts, not ambient API-key/Bedrock/Vertex/Foundry setups.
Provider CLI/keychain semantics still apply; raw auth storage is never inspected.

## Remaining allowance and reset times

Each account groups login/live status with readable session/weekly remaining
percentages and reset times labeled UTC. Only windows with usable remaining
allowance are shown; unavailable windows and reset-only rows are omitted. If no
window is usable, only login/live results appear for that account. One UTC
timestamp at the report end means local report completion, not simultaneous
measurement of the accounts. Raw source
identifiers, window-minute fields and repeated credit notices are omitted. Codex uses its supported
`account/rateLimits/read` interface through one bounded stdio app-server process
in the selected home. It sends initialization and the account read only; it
creates no thread or model turn. The app-server uses its own account/config
semantics; the live probe's ignore-config flags do not apply to this process.

Window duration determines the label: a positive duration below 24 hours is
`session`; 10080 minutes is `weekly`. Primary/secondary positions are not assumed
to mean session/week. Remaining is 100 minus a valid provider percentage. Only
the `codex` bucket is selected when multiple buckets are returned. Missing,
unsupported or ambiguous windows and invalid percentages are unavailable. A reset
at or before sample observation makes remaining unavailable and hides that row.
An absent or invalid reset is independently shown as not reported even when a
percentage is available.
Sample observation remains local check completion time internally for stale
validation; the final report timestamp is not proof of server-data freshness.

Claude collects public `rate_limit_event` fields from its existing live ping
stream; it makes no additional model request. A reported `five_hour` window maps
to session and `seven_day` to weekly. Fractional utilization becomes remaining
percentage. Model-specific limits, overage, token counts, costs and purchased
credits are never converted into aggregate subscription allowance. Credits stay
separate and their balance is not displayed or used.

These events may describe only the currently limiting window. A successful ping
does not guarantee either or both windows. Missing fields remain unavailable;
invalid/stale percentages, conflicting samples and missing/mismatched session
attribution never invent an allowance. Repeated identical samples are accepted.
The terminal result still determines live success, independently of quota data.
For a full human report, enter `/usage` in the selected Claude account. The helper
does not invoke that report, experimental snapshot requests or internal window
fields, and does not scrape terminal output or credentials.

Usage is informational and does not change the aggregate login/live exit code.
A timeout, missing CLI, RPC error or malformed response leaves usage unknown
internally and omits its rows; it is not an authentication verdict. Login/live
failures and their sanitized diagnostics remain visible. Codex runs up to three
bounded subprocesses per account (login, live, usage); Claude runs two. The same
time, output and process-group cleanup bounds apply to the usage query. No raw
RPC response or server diagnostic is printed.

The interfaces are described in the official
[Codex app-server documentation](https://learn.chatgpt.com/docs/app-server) and
[Claude status-line documentation](https://code.claude.com/docs/en/statusline).
Claude event names and fractional units are also documented in the official
[SDK types](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)
and [wire parser](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/_internal/message_parser.py).
Support was assessed from these references and installed source/help, without an
author live account read. Installed CLI or provider differences can leave usage unavailable.

## Verification and interface references

Fake CLI suite (no live calls):

```sh
python3 -B -W error::ResourceWarning -m unittest discover -s tools -p test_provider_checks.py -v
```

The suite executes the real just recipe with fake CLIs and a disposable writable
XDG runtime directory. It covers spaces in paths, home selection, mixed results,
missing configuration/CLI/home, output bounds, timeout and interruption cleanup.
Usage cases cover the RPC handshake, notifications and unrelated response IDs,
reordered durations, invalid/stale values, missing buckets/windows, credits-only
data, server errors, early exit, malformed output and timeout descendant cleanup.
Claude cases also cover sparse events, session attribution, conflicting samples,
terminal failures, and collection from the existing ping without another process.
A parser-based Claude fake models variadic options and the positional prompt;
the old undelimited vector must fail while the corrected vector succeeds. This
is deterministic grammar coverage, not execution of Claude itself or proof of
the cause of any particular live failure.

CLI forms were checked against installed `codex exec --help`, `codex login
--help`, `claude --help`, and `claude auth status --help`, plus the official
[Codex command reference](https://developers.openai.com/codex/cli/reference),
[Codex non-interactive reference](https://developers.openai.com/codex/noninteractive)
and [Claude CLI reference](https://code.claude.com/docs/en/cli-reference).
