# Finding: add official Gemini ACP as the `impl2` route

## Origin — 2026-08-18

The Antigravity ACP investigation established that the installed `agy` has no
Google-supported ACP boundary and must not be wrapped through Slawomir's
Antigravity OAuth session. Google's official Gemini CLI is installed and
authenticated separately and advertises native ACP over JSON-RPC/stdio.

Slawomir confirmed that Gemini integration remains a go. This record carries
that implementation independently so the Antigravity limitation Work can
close without losing the approved continuation.

## Confirmed operating model

- The visible implementation endpoint remains `baton.impl`.
- The existing internal route `impl`, handled by `baton.claude`, remains the
  primary and deterministic default.
- Add internal backup route `impl2`, handled solely by `baton.gemini`.
- Selecting Gemini is explicit per Work. Omitted route selection continues to
  resolve to `impl`; Baton never automatically fails over, races both agents,
  or displays every candidate route on a Work row.
- Gemini holds the existing `impl` role but uses its own participant identity,
  ACP bridge process, session/state directory, authentication, permission
  mode, and deployment-owned deny policy.
- Claimed Work never moves underneath its Handler. It must first be released
  or passed, then rerouted and claimed normally.

## Acceptance

- Configuration accepts one visible kind with a deterministic default route
  plus one or more explicitly selectable backup routes.
- Handoff with no route selects `impl`; explicit `route=impl2` selects Gemini;
  an unconfigured or role-incompatible route refuses atomically.
- The selected route is recorded in authoritative Events and is the only route
  projected for that Work.
- `baton.gemini` runs through the deployed generic ACP bridge using
  `gemini --acp`, separate state, and a deployment-owned deny policy.
- A canary proves initialization/authentication, new and resumed sessions,
  permission enforcement, one wake/claim/pass cycle, cancellation, restart,
  and clean shutdown.
- Existing Claude `impl` assignments and default behavior remain intact.

## Relationship

Follow-up to W163 and
`work/records/2026/08/finding-antigravity-acp-trial/`. W163 owns the evidence
that Antigravity cannot be integrated safely today; this record owns the
approved Gemini implementation.
