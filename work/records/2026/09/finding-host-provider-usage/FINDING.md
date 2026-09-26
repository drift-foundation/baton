# Host allowance reporting — W266071

## 2026-09-25 — owner acceptance and separate Claude collection investigation

Owner accepts the independently reviewed readability improvement and selects a separate bounded follow-up for Claude usage collection. This does not claim the newly formatted live command was rerun. Review evidence remains review-2026-09-25T13-44-39Z.md. Ledger closure remains an owner action.

Owner supplied an interactive Claude `/usage` report from the ACP-configured account: session 13% used, weekly all-models 58% used, with reset times; these are historical owner observations. Therefore the missing automated data is a checker collection gap, not proof that Claude CLI or the ACP account lacks usage information. The separate follow-up must establish a supported bounded collection interface or return an exact limitation and manual command. Do not scrape changing terminal layout, inspect credential contents, call undocumented account endpoints, or expand into v12. Implementation is not selected by this investigation; return a concrete recommendation first.

2026-09-25, owner266168 following accepted W265097; tuner claim266170.
Confirmed scope: add provider-reported short/session and weekly remaining
percentages, reset times and observation times to the aggregate host checker.
No author/reviewer live probes, auth-file scraping, v12 mode or framework.
Preserve existing checks, account selection, environment isolation and bounds.

## Source assessment and selected implementation

[Codex app-server documentation](https://learn.chatgpt.com/docs/app-server)
specifies account/rateLimits/read after initialize/initialized. Its quota windows
carry usedPercent, windowDurationMins and resetsAt (epoch seconds); multiple
buckets can occur. Use the codex bucket only, map durations rather than positions,
and calculate remaining as100-used for validated percentages. No thread/turn,
login or credit redemption request is needed. Installed app-server help confirms
stdio transport. No real server/account read was executed during preparation.

[Claude status-line documentation](https://code.claude.com/docs/en/statusline)
describes five_hour/seven_day usage and reset fields after a response, but this
is not evidence of availability in print-mode output. No supported noninteractive
allowance source is established here. Report unknown/unsupported without calling
undocumented endpoints, reading credentials or treating token cost as allowance.

Tuner owns tools/provider_checks.py, tools/test_provider_checks.py,
docs/PROVIDER-CHECKS.md and this new dossier. justfile unchanged. Existing login/
live checks remain authoritative for their aggregate exit status; allowance is
additional information. Unsupported/unavailable/stale/malformed allowance is
explicitly unknown and does not turn a successful host check into an auth failure.
Display UTC local observation time (not a claim of server snapshot freshness),
actual window minutes and separate reset time; expired reset invalidates remaining.
Short means positive duration under24h; weekly means10080 minutes; other or
ambiguous windows remain unknown. Purchased credits are explicitly separate and
not converted into subscription percentages. Raw server diagnostics remain hidden.

Bound one extra short-lived stdio server per Codex account to existing per-check
time/output limits, send only initialize, initialized and account/rateLimits/read,
then terminate its process group. Correlate response IDs; do not accept update
notifications or unrelated responses as the requested snapshot. Tests use fake
CLIs including sequencing, missing windows, reordered durations, invalid/stale
values, credit-only data, errors, output bounds and timeout cleanup.

## 2026-09-25 — owner selects human-readable presentation

Owner ran the aggregate task: all four host accounts pass login/live; Codex weekly values reported48% and100%, short-window data unavailable; Claude usage source unsupported. These are owner-reported observations, not repeated agent probes. Owner states output is for humans, not parsing, and rejects the verbose key=value report.

Supersede the earlier default rendering requirement for repeated unknown fields, raw source names/window minutes and per-account credit notices. Use a compact labeled account summary with login/live status, reported allowance and readable timezone-labeled reset times. State missing session data briefly when another window is reported; collapse wholly unavailable usage into one short explanation. Show observation time once per account/report as appropriate without implying server freshness. Omit repeated purchased-credit disclaimers from normal output; preserve the distinction in docs. No new machine-output format is requested.

Earlier owner preference also stands: supported structured API fields may be rendered; do not scrape unstable provider text into percentages. A future provider-native usage report may be displayed only through an established safe usage-report interface, not arbitrary stdout/stderr. This presentation correction requires no new provider source, Claude usage implementation or live calls. Keep classifications, validation, account isolation, timeout behavior and exit semantics intact. Update focused rendering tests/docs and return for independent review.
