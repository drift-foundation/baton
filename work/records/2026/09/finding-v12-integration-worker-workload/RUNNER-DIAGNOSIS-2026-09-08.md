# Repeated ACP turn completion before handoff

2026-09-08 — baton.prompt, interactive operational investigation requested by
Slawomir after repeated recovery made progress crawl. Read-only investigation;
no test run, claim, recovery, reroute or runner restart performed.

## Observed

The deployment log `/home/sl/baton-v11.14aecfb/log/claude-acp.log` records
five turns ending with a progress/status response while verification or handoff
was still outstanding. These correspond to incidents 35–39:

| Work / assignment episode | Evidence immediately before domain teardown |
| --- | --- |
| W110935 / 113665 | Says PROGRESS and pass remain to do once the gate reports; teardown at log line 2820097. |
| W110935 / 114003 | Says the gate is re-running and promises progress/handoff when it reports; teardown at 2821869. |
| W110935 / 114108 | Says it will wait rather than poll and promises the pass after the gate; teardown at 2829304. |
| W110935 / 114423 | Ends with "Waiting on the gate"; teardown at 2832475. |
| W114085 / 114284 | Ends with a correction recap while the required gate runs; teardown at 2838586. |

All five identify session ba1f4305-938c-4aa8-97e8-f3c8595b907a and bridge
incarnation 44749090-e10c-424a-bd91-67b4ddcc9065. Releases clear the settlement
fence; subsequent session-ready records name the same session. An intervening
W114085 / 114085 turn did hand off successfully, so "every turn fails" is not
literally supported. The previous c46b5830 session also has successful deliveries.

## Mechanism established from source

`tools/acp-baton-bridge/src/acp_baton_bridge.mjs` awaits `live.promptText`, then
calls `settleDomain`, then examines the canonical claim slot. A surviving claim
produces the failed state and incident through `acp_settlement.mjs`. The log's
"domain torn down after delivering" lines correspond to that returned-prompt
path. Death and configured-deadline exceptions take separate paths in
`acp_agent_session.mjs` and the bridge.

In incidents 35 and 37 the ACP connection/query cleanup errors appear AFTER
domain teardown. Those errors do not establish an initiating model crash.
The exact ACP stop reason is not present in the inspected log excerpts.

## Inferred and open

The immediate failure is premature completion of a managed turn while holding
Work, apparently expecting a later background-tool completion to resume it.
Repeated release/reload does not correct that completion behavior. Whether the
behavior originates in model choice, session context, adapter/tool semantics or
an interaction among them remains open; a model or SDK regression is not proved.
The onset is associated with the newer session, but that correlation is not
causation. No claim is made that all broad runs were needed or redundant.

## Proposed operational disposition

At a safe handoff, explicitly assign the bounded remaining correction to the
idle tuner, with exact file ownership and scheduled test-change authority,
retaining baton.codex as independent reviewer. Reuse completed gates; targeted
verification must answer named remaining questions. Investigate the K/ACP
completion behavior separately instead of repeatedly spending product turns on
the same release/retry cycle. This is a recommendation, not an enacted allocation.

During inspection W114085 had already reached baton.codex review, while K resumed
W110935 and acquired its live claim. Do not split or reassign underneath that
claim without coordinated recovery and execution quiescence.
