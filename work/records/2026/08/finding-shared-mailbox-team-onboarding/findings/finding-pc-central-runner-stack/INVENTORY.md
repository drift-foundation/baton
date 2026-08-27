# W10198 central-stack inventory

Revalidated on 2026-08-25 against the live, read-only inputs under
`/home/sl/baton-v11.14aecfb/` and the accepted generation-2 `baton.json`.

## Preserved Baton topology

The successor keeps these entries byte-for-byte equal to the live manifest:

- contexts `prompt` (`baton.prompt`), `reviewer` (`baton.codex`), and `tuner`
  (`baton.tuner`);
- services `codex-app-server`, `codex-dispatcher`, `codex-readiness`,
  `codex-tuner-readiness`, and `claude-acp` (`baton.claude`);
- control identity `baton.slaw`, binary, configuration, app-server endpoint,
  dispatcher socket, and all existing dependency edges.

The live manifest already contains no Gemini service. The successor introduces
no Gemini string in its manifest, dispatcher template, or ACP template.

## Pushcoin additions

| Participant | Role | Context/Service | Readiness target | Working directory | Log locator |
|---|---|---|---|---|---|
| `pc.prompt` | `prompt` | context `pc-prompt` | none | `/home/sl/src/pushcoin` | `log/context-pc-prompt.log` |
| `pc.plan` | `rview` | context `pc-plan`; service `pc-plan-readiness` | `pc-plan` | `/home/sl/src/pushcoin` | `log/context-pc-plan.log`; `log/pc-plan-readiness.log` |
| `pc.tuner` | `tuner` | context `pc-tuner`; service `pc-tuner-readiness` | `pc-tuner` | `/home/sl/src/pushcoin` | `log/context-pc-tuner.log`; `log/pc-tuner-readiness.log` |
| `pc.code` | `impl` | service/render `pc-code-acp` | ACP `wait` | `/home/sl/src/pushcoin` | `log/pc-code-acp.log` |
| `pc.slaw` | `approv` | no runner | none | n/a | none |

The dispatcher maps the three Codex contexts one-to-one:

| Target | Participant | Thread placeholder | Action owner |
|---|---|---|---|
| `pc-prompt` | `pc.prompt` | `{{context.pc-prompt.threadId}}` | `pc.slaw` |
| `pc-plan` | `pc.plan` | `{{context.pc-plan.threadId}}` | `pc.slaw` |
| `pc-tuner` | `pc.tuner` | `{{context.pc-tuner.threadId}}` | `pc.slaw` |

`pc.code` uses a fresh state path on every lifecycle start at
`run/acp/{{start.id}}/pc.code`. Its Claude configuration and hard Git guard are
participant-local under `/home/sl/.local/state/acp-baton-bridge/pc.code/` and
`/home/sl/.config/baton/acp/pc.code/policy/`. The kernel boundary protects the
actual Pushcoin Git metadata path `/home/sl/src/pushcoin/.git` read-only.

The corrected ACP template exports `BATON_BIN`, `BATON_CONFIG`,
`BATON_PARTICIPANT=pc.code`, and `BATON_ROLE=impl` to the isolated agent and
the verifier requires exact equality with the template's canonical `baton`
object. The isolated Claude profile keeps its deployment-owned
`.credentials.json` outside the repository; the operator recipe requires a
non-empty mode-600 file before start and never prints or packages it.

## Staged artifacts

The literal-install successor set is in `successor/`:

- `infra.json` and `codex-event-bridge.template.json`;
- `acp-pc-code.template.json`;
- generated `baton.rules` for all six Codex targets plus the deployment-wide
  Docker inspection profile;
- `pc-code-policy/`, including the friendly hook and fail-closed bubblewrap
  boundary;
- `pushcoin-AGENTS.md`, the literal protocol-11 durable-policy successor that
  must be installed and verified before the new runners start;
- `verify.py`, `verify.mjs`, and `INSTALL.md`.

The initial successor is live. The post-smoke locator/policy correction is
staged and deliberately awaits the operator reconciliation boundary in
`successor/INSTALL.md`; until then the live ACP template and Pushcoin policy
are expected not to byte-match those two corrected successors.
