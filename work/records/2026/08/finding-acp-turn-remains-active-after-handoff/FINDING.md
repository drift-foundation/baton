# ACP turn remains active after its Work handoff

## Observed — 2026-08-29

The deployed `dd1dc3e` `baton.claude` ACP runner completed its W29400 work,
passed W29400 to review at sequence 38976, and emitted a final recap. W29400
subsequently closed satisfying at sequence 39048. The same runner nevertheless
continued publishing `state=working`, `work=W29400`, and served no later turn.

W38956 passed to `baton.impl` at sequence 39022 and remained ready, unclaimed,
and `pickup=overdue`. Poke 38978 to `baton.claude` also remained pending. At
06:44 MDT the ACP bridge PID 2756087 and its Claude child were alive and
sleeping, while `claude-acp.log` had not advanced since 06:24:47 MDT. The log
ended after the W29400 pass, a final answer, and stale terminal-waiter notices;
it did not record a new W38956 delivery.

This is not a Work dependency or scheduling choice. W38956 has no blocker and
is the high-priority head offer for `baton.claude`. It is also not evidence
that W11910's claim-aware offer retention alone failed: the preceding ACP turn
never returned to an idle/deliverable state from the bridge's perspective.

## Expected

After an agent has handed off its claimed Work and emitted its terminal answer,
the ACP turn must reach one bounded terminal state. The adapter must publish
idle, re-arm readiness, and deliver the next canonical offer. A transport or
provider session that does not acknowledge completion must become a visible
failed/wedged runtime with actionable diagnostics rather than remaining
healthy-looking `working` on closed Work forever.

## Immediate boundary

This finding records the defect before any operational workaround. A managed
stack restart may recover W38956, but is not the fix. Do not expand the current
v12 dogfood milestone to repair this v11 runner: W38956 remains the high-
priority critical path, while this follow-up stays lower priority unless the
restart cannot restore delivery.

## Reviewer revalidation — 2026-08-29

**Confirmed:** this incident is the live `baton.claude` deployment still
running the pre-W28681 bridge, not a missing recovery path in the current
source. PID 2756087 started at `Thu Aug 27 22:28:10 2026`; its bridge, launcher,
ACP adapter, and Claude child retained the same process chain through this
review. The repository correction for W28681 was committed later in
`be1e170` on 2026-08-29.

**Confirmed:** the installed
`/home/sl/opt/baton/v11/dd1dc3e/lib/acp-baton-bridge` implementation races an
ACP prompt only against agent death. Its own comment says a turn has no work
deadline. The active
`/home/sl/baton-v11.14aecfb/run/context/claude-acp.json` has
`setupTimeoutMs=90000` and `retryMs=2000` but no `turnTimeoutMs`. The installed
launcher is the earlier mount-only bubblewrap boundary; it has neither
`--unshare-pid` nor `--die-with-parent`, and the active policy does not include
W28681's process-domain preflight.

**Confirmed:** current source already implements the required
restart-independent recovery under W28681. `AcpAgentSession.promptText()` races
the prompt and agent death against the mandatory wall-clock `turnTimeoutMs`.
On expiry, `runBridge()` positively tears down the per-turn process domain,
publishes correlated `failed/cause=internal`, retains the readiness key, backs
off, and polls again. Focused tests drive both a silent prompt that never
settles and one that keeps emitting valid ACP updates; neither can extend the
deadline. Normal work handoff is deliberately not a terminal signal because
an agent may validly pass before completing its final response.

**Confirmed deployment drift:** `conf/acp-bridge.template.json`,
`conf/acp-claude.template.json`, and `conf/acp-gemini.template.json` all omit
the now-mandatory `turnTimeoutMs`. Rendering one unchanged and starting the
current bridge therefore fails configuration validation instead of recovering
the lane. W28681 updated the separate pc.code successor template, but not
these repository-level lifecycle templates or the already-running
`baton.claude` service.

**Supersession:** the earlier acceptance wording must not be read as approval
for a second post-handoff watchdog or for deriving ACP completion from Work
state. W28681's fixed wall-clock deadline is the confirmed recovery boundary;
its duration remains explicit deployment policy. The actionable defect here
is activation: align the shipped templates with that mandatory schema, then
release and cut over `baton.claude` to the reviewed bridge, launcher, config,
and process-domain preflight as one fail-closed change.

## Acceptance

- Reproduce an ACP turn that emits its final response after passing its Work
  but never yields terminal completion to the bridge.
- Bound the completion wait and publish a typed unhealthy runtime state naming
  the participant, session, prior Work and cause.
- Preserve the ready Work offer and deliver it after safe recovery without a
  second claimant or cross-participant delivery.
- Prove normal long-running turns are not interrupted merely because Work was
  handed off before the provider finishes its final response.
- Cover restart recovery and a restart-independent recovery path if v11 keeps
  one; automatic replacement remains v12 Worker Manager scope.

The first, second, third, and fifth clauses are already covered by W28681's
reviewed implementation and focused matrix. For this follow-up, acceptance is
the missing deployment crossing: all shipped ACP templates carry an explicit
operator-selected `turnTimeoutMs`; the installed bridge and launcher match the
reviewed process-domain boundary; the exact service-context preflight passes;
the old process domain is positively gone; and one live smoke shows the
preserved next canonical offer delivered without duplicate claim.
