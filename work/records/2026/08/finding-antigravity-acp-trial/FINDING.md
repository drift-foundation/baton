# Finding: Antigravity has no supported ACP boundary yet

## Request

Slawomir installed and authenticated Google Antigravity CLI (`agy`) and asked
to add it as another agent behind Baton's generic ACP readiness bridge.

## Observed — 2026-08-18

- The installed executable is `/home/sl/.local/bin/agy`, version `1.1.14`.
- Its local command reference exposes text and persistent NDJSON
  `stream-json` input/output modes, but no ACP subcommand or `--acp` flag.
- Google's open `google-antigravity/antigravity-cli` issue 31 requests a native
  ACP JSON-RPC/stdio mode. The requested mode is therefore roadmap work, not a
  capability advertised by the installed release.
- Google's Antigravity Terms state that third-party software, tools, or
  services must not use Antigravity OAuth to access the service and warn that
  doing so may cause account suspension or termination.
- Unofficial ACP adapters exist, but they either wrap `agy` print/stream modes
  or inspect Antigravity's private conversation state. They are neither a
  Google-supported ACP surface nor an acceptable boundary for this deployment.
- Google's official Gemini CLI separately advertises native ACP over
  JSON-RPC/stdio with `gemini --acp`. No `gemini` executable is installed on
  this host at the time of this finding.

## Confirmed boundary

Baton must not point a custom or third-party ACP adapter at Slawomir's
authenticated Antigravity OAuth session. In particular, this finding does not
authorize wrapping `agy --input-format stream-json`, scraping Antigravity's
conversation database, copying credentials, or bypassing its interactive
permission model.

The existing `acp-baton-bridge` remains the correct model-neutral Baton
boundary. It may launch Antigravity only when Google ships an official native
ACP entry point, or launch a different Google-owned client that officially
implements ACP under its own supported authentication contract.

## Decision required

Choose one supported continuation:

1. wait for Google to ship native `agy --acp`, then certify it against the
   generic bridge; or
2. install and authenticate Google's official Gemini CLI and certify
   `gemini --acp` now, using a separate Baton participant, session, state
   directory, permission mode, and deployment-owned prohibition policy.

A Google Cloud/API-key or Vertex-backed agent could be evaluated as a third
option, but it is a different credential and service contract; it must not be
silently substituted for the authenticated `agy` session.

## Decision — 2026-08-18: certify official Gemini CLI

**Confirmed by Slawomir through installation and authentication.** Proceed
with option 2 using Google's official Gemini CLI and API-key authentication.
Do not adapt or invoke the authenticated `agy` session through Baton.

Local revalidation after installation:

- executable: `/home/sl/.nvm/versions/node/v24.14.0/bin/gemini`;
- version: `0.55.1`;
- native server entry point: `gemini --acp`;
- explicit execution controls: `--approval-mode`, `--policy`, and
  `--admin-policy`.

The canary uses a new `baton.gemini` participant holding the existing
implementation role, but a dedicated canary route/kind whose sole handler is
that participant. It must not be added to the production implementation route
or share Claude's bridge state/session. Certification proves the official ACP
surface, API-key authentication, session new/load, one Baton assignment cycle,
cancellation, and a deployment-owned deny policy before any production route
change is considered.

## Route naming and operating decision — 2026-08-18

**Confirmed by Slawomir.** Claude and Gemini remain members holding the same
`impl` role, but they receive separate explicit coding endpoints and routes:

- `baton.impl1` / route `impl1` has sole handler `baton.claude`. It is the
  primary, more capable, and more expensive implementation path.
- `baton.impl2` / route `impl2` has sole handler `baton.gemini`. It is the
  backup or deliberate alternate implementation path.

The ordinal names describe operator preference, not an automatic fallback
chain. Baton never silently transfers Work from one model to the other. A
handoff selects `baton.impl1` or `baton.impl2` explicitly, and each recipient
must claim normally.

This decision supersedes the generic final name `baton.impl`, but does not
authorize removing that live endpoint while Work still targets it. At the
time of this ruling seven open Work items use `baton.impl`, including an active
Claude claim. The safe cutover is therefore ordered:

1. certify Gemini through the isolated endpoint that will become
   `baton.impl2`;
2. drain or authoritatively reroute every open `baton.impl` assignment;
3. in one accepted configuration generation, replace the old Claude kind and
   route with `impl1`, retain the common `impl` role, and add the certified
   Gemini participant/kind/route as `impl2`;
4. restart the two independent ACP launchers against their own deployment
   configuration and state, then prove one explicit assignment through each.

No compatibility alias remains after the cutover. Historical Events keep the
endpoint names committed at the time; new Work uses only `baton.impl1` or
`baton.impl2`.

## Superseding clarification — 2026-08-18: route selection is per Work

**Approved by Slawomir. The preceding two-endpoint cutover is superseded.**
It incorrectly exposed internal implementation routes as separate public
kinds. Baton keeps one visible implementation kind/endpoint: `baton.impl`.

That kind permits two internal routes under the existing `impl` role:

- `impl1` has sole handler `baton.claude` and is the default route;
- `impl2` has sole handler `baton.gemini` and is the explicit backup or
  alternate route.

Route selection is authoritative per Work assignment. Passing to
`baton.impl` without an override selects `impl1`; passing with
`route=impl2` deliberately selects Gemini. The chosen route is recorded in
the handoff/Event history and the Work projection. The UI shows only that
selected route and, after claim, the actual Handler. It never presents both
candidate routes on one Work row.

There is no automatic failover or race between handlers. If `impl1` is
unavailable, an operator explicitly selects or reroutes eligible unclaimed
Work to `impl2`. Claimed Work cannot move underneath its Handler: it must be
released or passed before rerouting.

The configuration declares the allowed route set and its default for the one
`baton.impl` kind. A per-handoff override is accepted only when the route is
configured for that kind and carries its required role. Omitted selection
resolves deterministically to the configured default inside the same
authoritative mutation; clients never infer it independently.

## Naming clarification — 2026-08-18: retain `impl` as the primary route

**Approved by Slawomir; this supersedes `impl1` as the primary-route name.**
There is no need to rename the established Claude route. The general model is
one primary route and any number of configured backup routes:

- visible kind/endpoint: `baton.impl`;
- default internal route: `impl`, currently with sole handler
  `baton.claude`;
- backup internal routes: `impl2`, `impl3`, and so on, each selected
  explicitly for a particular Work; the first canary assigns Gemini to
  `impl2`.

The number of backups is not fixed at one. Configuration declares an ordered,
unique allowed set with exactly one default. Omitting `route=` selects `impl`;
`route=impl2` (or another configured backup) selects that route for this Work.
Only the selected route is projected and shown. No client displays every
candidate route on the Work row, and no candidate is tried automatically.

## Final disposition — 2026-08-18

**Confirmed by Slawomir in T163.** Postpone Antigravity integration until
Google offers a proper supported ACP surface. Do not build or certify an
unofficial adapter around `agy`; use the official Gemini client for current
Google-agent experiments.

Slawomir recommends closing this Antigravity decision Work. Closing W163 does
not certify Gemini or silently complete the unimplemented route-selection and
canary steps below; any continued Gemini integration must be carried by its
own separately accountable Work.

## Clarification — 2026-08-18: Gemini remains approved

**Confirmed by Slawomir.** “Use Gemini for now” is an approved implementation
direction, not a deferral. Gemini must be added as the explicit `impl2` backup
route while the existing Claude `impl` route remains the default. That work is
split into the separately bound Gemini ACP/`impl2` Work so closing this record
ends only the unsupported Antigravity path.

## References

- <https://github.com/google-antigravity/antigravity-cli/issues/31>
- <https://antigravity.google/terms>
- <https://antigravity.google/docs/cli-install>
- <https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/acp-mode.md>
- <https://github.com/google-gemini/gemini-cli/blob/main/docs/get-started/installation.mdx>
