# Effective Baton adoption guide

Status: **implemented and independently approved; deployment announcement delivered; awaiting commit**.

Discovery context: immediately after RC 1.0.0 was committed and released,
Slawomir asked for a release announcement teams can share and a concise guide
to using Baton effectively, including the durable `work/finding-*` workflow.

## Confirmed boundary

- Add a path-neutral `docs/EFFECTIVE-BATON.md` for teams adopting Baton.
- Keep `README.md` authoritative for the full CLI/storage contract and
  `docs/AGENTS-MAILBOX-PROTO.md` authoritative for protocol and mailbox
  conventions. The new guide links to them and organizes a working routine; it
  does not restate every option or schema rule.
- Cover onboarding, the active wait/claim/reply-or-close loop, notices,
  subjects/tweets/references, materialization, and failure-safe operations.
- Explain a recommended finding workflow clearly as repository/team policy,
  not Baton protocol enforcement: decisions are pinned before implementation,
  findings/plans/progress/review journals preserve restart context, and
  handoffs reference exact files.
- Include development isolation: normal users stay on the canonical released
  zipapps and live authority; candidate builds and protocol experiments use a
  separate distribution path and separate development authority until a
  reviewed release gate.
- Add a short path-neutral 1.0.0 release announcement in `docs/` and deliver a
  ready-to-share deployment-specific version to Slawomir through Baton.
- Link the two new documents near the front of the README without duplicating
  agent-only policy from `AGENTS.md`.

No code, protocol, schema, authority, config, or generated artifact change is
authorized by this finding.

## Resolution

K independently reviewed the guide, path-neutral release announcement,
deployment-specific announcement, links, and every documented command against
the 1.0.0 parser. One required correction now states the actual generation+1
`regen` workflow; the ambiguous frozen protocol wording is queued separately
in `work/finding-config-regen-wording/`. The guide also records first-hand
Claude monitor and Codex live-turn behavior without treating either as Baton
protocol.

Focused documentation/distribution checks pass, released artifacts/manifests
remain unchanged, and the reviewed deployment announcement was delivered to
Slawomir through Baton.

## Acceptance evidence

1. Examples use participant-only protocol 10 syntax: no actor or seed.
2. Every command uses an explicit executable and absolute config placeholder.
3. The guide says `wait` is read-only, exact claim follows a reported message
   id, notices use `see`, and every claim ends in `reply` or `close`.
4. Findings are presented as recommended team policy rather than protocol
   behavior.
5. The release announcement does not imply Internet, daemon, central service,
   or application-level authentication.
6. Repository links resolve and `git diff --check` passes.
