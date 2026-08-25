# Shared mailbox team onboarding

## Confirmed decisions — 2026-08-25

Slawomir approved bringing these repository teams into the current v11
coordination authority:

| Root | Team | Repository |
|---|---|---|
| `orch` | `orch` | `/home/sl/src/build-orchestrator` |
| `lang` | `lang` | `/home/sl/src/drift-lang` |
| `maria` | `maria` | `/home/sl/src/drift-mariadb-client` |
| `tls` | `tls` | `/home/sl/src/drift-net-tls` |
| `query` | `query` | `/home/sl/src/drift-query` |
| `web` | `web` | `/home/sl/src/drift-web` |
| `uflow` | `uflow` | `/home/sl/src/drift-workflows` |
| `pc` | `pc` | `/home/sl/src/pushcoin` |

The existing `baton` participant names remain unchanged. Every new team uses
provider-neutral participant identities:

- `<team>.prompt`: human-attached interactive copilot, not routable;
- `<team>.plan`: research, planning, coordination, and independent review;
- `<team>.code`: primary implementation;
- `<team>.slaw`: team approval and abandoned-claim recovery;
- `<team>.tuner`: documentation and final polish.

The new teams use the same role and kind vocabulary as Baton, with routes
`approv -> slaw`, `rview -> plan`, `impl -> code`, and `tuner -> tuner`.
Provider selection is runtime state, not part of the participant address:
`plan` is currently Codex-backed and `code` is currently Claude-backed.

Slawomir is one human shared across the teams but v11 addresses workflow
authority through team-scoped participants. Only `baton.slaw` retains the
instance-wide `config` and `dispatch` capabilities. Each new `<team>.slaw`
holds its local `approv` role and the narrow `recover` capability; duplicating
global administration across every team identity would overstate their scope.

Gemini is removed from this deployment. The accepted successor configuration
must remove `baton.gemini`, the `impl2` route, and `impl`'s `impl2` alternate.
The matching lifecycle successor must omit the `gemini-acp` service. Generic
Gemini support may remain in the Baton distribution; this ruling removes it
from Slawomir's deployed team topology, not from the product.

## Operational boundary

All teams share one SQLite coordination authority, but runners remain
repo-local. Adding a team to `baton.json` does not launch its agents in the
Baton repository's lifecycle stack. Each repository will later supply its own
contexts, readiness producers, ACP bridge, execution policy, and working
directory. This avoids one central restart eagerly creating 24 Codex contexts
and eight Claude sessions.

The currently accepted configuration must not be edited in place while the
stack is live: a generation-2 proposal is not accepted authority until
`regen`. Prepare successor files separately, then drain, stop, install the
proposal, run `regen`, and restart.

## Acceptance

- The successor config validates as generation 2 and adds exactly the eight
  roots and eight teams above.
- Existing Baton Work remains routed through `baton.codex` and
  `baton.claude`; no existing Baton participant is renamed.
- No Work is held by `baton.gemini` at cutover.
- The successor lifecycle manifest starts no Gemini service.
- A post-restart `teams` read shows the new members offline until their own
  repository runners are deployed; offline is truthful and expected.
