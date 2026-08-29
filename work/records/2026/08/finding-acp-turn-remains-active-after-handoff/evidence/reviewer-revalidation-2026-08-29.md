# Reviewer revalidation — 2026-08-29

## Live process and installed boundary

Read-only process inspection found:

```text
PID      PPID     STAT  STARTED
2756087  1        Ssl   Thu Aug 27 22:28:10 2026
2756376  2756087  S     Thu Aug 27 22:28:59 2026
2756379  2756376  Sl    Thu Aug 27 22:28:59 2026
2756391  2756379  Sl    Thu Aug 27 22:28:59 2026
```

PID 2756087 runs:

```text
node /home/sl/opt/baton/v11/dd1dc3e/lib/acp-baton-bridge/src/acp_baton_bridge.mjs --config /home/sl/baton-v11.14aecfb/run/context/claude-acp.json
```

The installed `acp_agent_session.mjs` says a turn has no arbitrary work
deadline and awaits only this race:

```text
Promise.race([turnDone, death])
```

The active config exposes `setupTimeoutMs=90000` and `retryMs=2000`; searching
it for `turnTimeoutMs` finds no member. The installed policy launcher ends in a
mount-only `bwrap` invocation. It contains neither `--unshare-pid` nor
`--die-with-parent`.

No signal, restart, config write, or live-service mutation was performed by
the reviewer.

## Current source boundary

Current source at `be1e170` contains W28681's correction:

- `tools/acp-baton-bridge/src/config.mjs` requires a positive bounded
  `turnTimeoutMs` with no default.
- `tools/acp-baton-bridge/src/acp_agent_session.mjs` races every prompt against
  that fixed wall-clock deadline.
- `tools/acp-baton-bridge/src/acp_baton_bridge.mjs` tears down the turn domain
  before reporting timeout, retains the readiness key, and resumes polling.
- `tools/acp-baton-bridge/test/acp_baton_bridge.test.mjs` drives both a silent
  never-settling prompt and a chatty never-settling prompt, requiring
  correlated `failed/cause=internal` and proving streamed activity does not
  extend the bound.

The reviewer ran `npm test` from `tools/acp-baton-bridge`: 89 tests passed,
zero failed. The existing environment diagnostic correctly reported that this
managed test context provides no PID namespace; W28681's exact host
service-context preflight, already preserved in its dossier, remains the
deployment gate.

The live bridge predates that correction. Its continued `working` projection
is therefore the exact old behavior W28681 replaced.

## Template crossing

The separate pc.code successor template records `turnTimeoutMs=3600000`, but
the three repository lifecycle templates do not contain the mandatory member:

```text
conf/acp-bridge.template.json
conf/acp-claude.template.json
conf/acp-gemini.template.json
```

This is not evidence that one hour is the correct `baton.claude` policy; the
W28681 ruling leaves the duration to the deployment. It is evidence that the
canonical lifecycle templates have not yet crossed the bridge's mandatory
configuration schema and cannot activate the reviewed recovery unchanged.
