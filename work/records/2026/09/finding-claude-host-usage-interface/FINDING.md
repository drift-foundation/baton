# Claude host usage collection interface — W266297

2026-09-25 owner thread266297; tuner claim266300.
Investigation only. Owner observed interactive /usage on the ACP-configured
account with session and weekly percentages and reset times. Missing automation
is a collection gap, not evidence that the account lacks usage data.

Read predecessor baton:work/records/2026/09/finding-host-provider-usage/FINDING.md
owner acceptance and review-2026-09-25T13-44-39Z.md. This separate Work does not
reopen or edit that accepted implementation, tests or progress.

Scope: installed CLI help/source and official documentation; establish a supported
bounded noninteractive interface or exact limitation plus manual command. Record
command/output shape and isolation constraints. No live provider calls, credential
contents, undocumented account endpoints, terminal-layout scraping, product edits,
v12 operations or broad tests. Own only this dossier. Review then owner decision.

## 2026-09-25 — investigation result, claim266300

Confirmed installed CLI2.1.263 has noninteractive /usage and structured
rate_limit_event support. Official SDK command documentation corroborates
noninteractive command dispatch; official Python SDK types/parser describe
public quota events. Full get_usage snapshot exists but is explicitly
experimental; unifiedWindows is labeled internal. Do not claim no interface
exists, nor promise both quota windows from public sparse events.

Proposed small change: collect public quota events from the existing live
probe using stream-json; preserve all safety/validation and unknown semantics.
No second model request. Native /usage is the manual full-report fallback;
its noninteractive report can include local activity details, so automatic
whole-output relay is not recommended without a further bounded design.
Exact command vectors, units, output shapes, byte-offset/source evidence,
account selection constraints and remaining limitations: RECOMMENDATION.md.
This proposal is decision support; no implementation was selected or made.

Operational finding: web retrieval of the TypeScript SDK reference failed
(over4MiB response; markdown fallback failed). Used official Python SDK source
and installed embedded source instead; do not claim TypeScript docs were read.
No local required file was unreadable. Research used read-only CLI help,
installed binary inspection and public official sources only. Zero live provider
calls, credential-content reads, transcript reads, tests or product edits.

## 2026-09-25 — owner selects partial collector, event266417

Supersedes investigation-only/no-product-edit scope above for this claim.
Owner selects the independently reviewed partial collector: change existing
Claude ping to bounded stream-json, use public rate_limit_event fields only,
no extra model request. Preserve terminal verdict, isolation, compact rendering
and unknown windows. No experimental get_usage, native-report fallback, scraping,
live author calls or v12 changes. Tuner owns tools/provider_checks.py,
tools/test_provider_checks.py, docs/PROVIDER-CHECKS.md and this dossier.
Revalidated current helper against recommendation/review: no prior Claude stream
collector exists. Implement deterministic parsing and per-stream session binding;
missing/contradictory attribution or conflicting same-window samples yield no
invented quota. Existing terminal success contract remains the live verdict.

## 2026-09-25T14-17-41Z — partial collector independently accepted after R1

[review-2026-09-25T14-17-41Z.md](review-2026-09-25T14-17-41Z.md) resolves R1: failed Claude streams without a unique terminal
result now retain recognized stdout diagnostics through sanitized classification.
The correction and two added regressions exactly account for the candidate
changes since prior review. All18 fake tests pass independently4.986s. Accepted
owner266417 implementation scope; return baton.decide. Sparse-window limitation
and manual selected-account /usage remain; no live provider proof or complete
snapshot guarantee. No product/test edits by reviewer.


## 2026-09-25 — owner selects one report-end timestamp

Owner live report: all four login/live checks pass; Codex weekly allowance reported; Claude session resets reported without usable percentages or weekly windows. Owner now requests one timestamp at report end, replacing repeated per-account Observed lines. This supersedes earlier per-account timestamp presentation only. Final timestamp denotes local report completion; retain sample times internally for stale checks. Tuner implements a small rendering/docs correction with focused deterministic verification and independent review; no new sources or live calls.

Owner follow-up: omit unavailable usage windows from human output, including reset-only windows without a usable allowance. This supersedes earlier visible unavailable-window explanations in default rendering; unavailable remains unknown internally, never zero/full allowance. Preserve login/live failures and their diagnostics. If no usage window is usable, show only login/live for that account. Keep one final report timestamp.

## 2026-09-25T14-25-20Z — owner266554 output changes independently accepted

[review-2026-09-25T14-25-20Z.md](review-2026-09-25T14-25-20Z.md) accepts omission of unavailable/reset-only usage rows and
one aggregate report-completion timestamp. Valid zero allowance still prints;
internal stale checks, unknowns and login/live diagnostics remain intact.
All18 fake tests pass4.586s. Return baton.decide; no live reviewer calls, new
source or v12 execution. Earlier presentation expectations are superseded by
the recorded owner selection; prior collector correctness acceptance remains.
