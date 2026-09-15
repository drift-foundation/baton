# Owner disposition — cap overrun and bounded remainder

Prepared by baton.codex under claim159669 at2026-09-13T10:09:12Z.
PROPOSED, NOT AUTHORITY. Current author cap remains780 cumulative seconds;
reviewer300 unchanged. Implementation verification is stopped pending disposition.

## Recorded incident

Author ledger240 runs sums exactly780.8047997559611s, exceeding the780 cap by
0.8047997559610849s. Final export step240 started with13.283701346038924s left and
used14.08850110200001s. The preceding export step238 had cost14.14424277299986s,
already more than that remaining allowance. The author's expectation that the
final export would fit was unsupported by the recent measurement. There was no
successful remaining-time guard. This is a verification-budget handling failure,
not a Baton protocol defect. Preserve all logs, the overrun and spending; do not
waive, round down, reset, or charge it to the reviewer. No further author execution
was reported after the overrun.

## Reviewable result and remaining acceptance

Independent review-2026-09-13T10-09-12Z.md accepts both orders' own B turns and
one observed, actually authorized terminal integration each.18 distinct retained
artifacts validate; the two extended orders each have66records, eight producer/
review completions plus one integration, at ticks24 and16. Three integrations
per order remain, plus requested correction, declared durable reopen and actual
engine/provider duplicate counters, and healthy-session evidence or exact refusal.
The combined two-repository/two-effective-slot contract, three product requirements
and locked-jsonschema gap remain. No full certification can be inferred or waived.

## Recommended owner decision

Record the overrun as an incident with all actual cost preserved. If continuing
the existing test-only evidence work is desired, approve author960 cumulative
seconds (180 above the prior cap), reviewer300 unchanged. At current actual
spending this leaves179.19520024403892s, not180s. No retroactive statement of cap
compliance. An alternative is to keep implementation stopped/park this Work while
retaining the accepted partial evidence and outstanding requirements.

Proposed additional subprocess envelope:

| Remaining work | Estimate |
| --- | ---: |
| Remaining three terminal imports in each order, actual receipts/result context and appropriate fake runtime state | 60s |
| Requested correction plus healthy-session evidence or exact owner refusal | 25s |
| Declared durable reopen with actual engine/provider counters and continued execution | 35s |
| Changed regression and one completed-candidate export | 30s |
| Bounded failed focused iterations, retained at actual cost | 20s |
| Total estimated new spending | 170s |

Reserve9.19520024403892s under proposed960. Estimates are not a guarantee of
completion or certification. Current two-order check costs5.2184s; export14.0885s;
composed class16.1626s. Do not repeat broad class/export after each partial edit.

Before EVERY subprocess, read cumulative ledger, compute actual remaining budget,
and set a timeout below that remaining amount with explicit overhead margin. Do
not start when the recent measured cost plus margin cannot fit; pick a narrower
needed selector or stop. Retain failure/timeout cost and inspect the updated
ledger before the next command. A timeout cannot promise zero wall-clock overhead;
stop/report any actual boundary breach rather than concealing it.

Same two new test files only: v12/python/tests/tools/scheduler_trace.py and
test_scheduler_trace.py.100logical ticks per trace; no live model, installation,
sleep, product/existing-test edit, Git mutation, acceptance reduction or budget
transfer. Reviewer remains at93.41752820399847/300s. Research0.2879257239692379s
separate. Pin any approved/amended ruling in FINDING/PLAN before dependent work.

## Approved disposition — recorded by review159755

Slawomir M159714 at2026-09-13T10:12:58Z approved this proposal including
per-command guards, author960/reviewer300, no reset/scope expansion/waiver.
This supersedes the opening pending/proposal-only current gate. Historical
overrun, estimates and then-current spending remain unchanged above.
