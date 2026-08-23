# Provenance of copied v11 material

This disposable prototype (Baton Work `W76`) is not Baton product source.
Where it reuses Baton v11 material it copies it here and modifies the copy.

It now lives in the Baton repository as the self-contained `v12/` subtree
(`finding-v12-in-repository-migration`), which changes where the files are and
nothing else: no module here imports from the v11 product tree, no v11 code or
recipe references this one, and every disposable path — authority, Job records,
attempt state, staged credentials, generated proof output — is written under
the external `state_root` in `poc.json`, never into the checkout.

Source repository: the enclosing Baton checkout (this subtree's parent)
Source commit: `8835cd5` (`feat(v11): harden coordination lifecycle and agent UX`)

| This root | Original repository-relative path | Commit | Modification |
| --- | --- | --- | --- |
| `src/baton_cli.mjs` | `tools/acp-baton-bridge/src/baton_readiness.mjs` | `8835cd5` | Rewritten around it: the `wait` argv shape, the readiness-is-an-edge rule, and the `episodeStillLive` re-read are the reused ideas; the shared `codex-event-bridge` envelope validator is NOT imported (that would couple to the live checkout) and is reimplemented locally against the same projection-12.3 field names. Extended with the mutating verbs the manager needs (`claim`, `pass`, `say`, `detail`, `bind`). |
| `src/acp_session.mjs` | `tools/acp-baton-bridge/src/acp_agent_session.mjs` | `8835cd5` | Copied structure: spawn/stdio JSON-RPC over the pinned official SDK, capability negotiation before session use, exact-permission-mode enforcement, permission-request-is-a-policy-failure, turn serialization, and v11's SETUP deadlines (initialize / session / mode). Modified: the agent subprocess is `docker run -i` rather than a host launcher; a manager-owned deadline supervises the TURN itself, which v11's setup supervision never did — v11 races a prompt only against the agent's death, and a live-but-silent agent here would hold the canonical Handler indefinitely (review round 2); the run-scoped `session.json` selection/persistence machinery of W27 is dropped (every prototype attempt is deliberately a fresh single-use session); update capture is structured for the trace instead of logged. |
| `node_modules/@agentclientprotocol/sdk` | (npm `@agentclientprotocol/sdk@1.3.0`) | — | Installed independently at the same pinned version v11 uses. Not copied from the checkout. |
| `src/input_source.mjs` | — (new) | — | Not derived from v11. Written for this prototype after review found that resolving an untrusted `job.in.json` source and copying it with `dereference: true` allowed a record-local symlink to materialize arbitrary host files into the worker snapshot. |
| `scripts/new-authority.sh` | `/home/sl/baton-v11.8835cd5/baton.json` (shape only) | — | The disposable authority document is modelled on the production one's structure. No production value, path, participant or database is reused. |

`src/authority/` (Baton Work `W2928`) is **not on this table on purpose**.
The disposable v12 assignment authority is new code written against
`finding-v12-assignment-state-machine/SPEC.md` version `1-ruled`, not a copy
or an adaptation of any v11 module. It reuses v11 CONCEPTS the specification
names — Route and Handler as separate questions, phase as a closed scheduler
axis, one displayed typed gate, compare-and-swap with an operation journal —
and no v11 code. Its schema is a fresh superset described by §5 of that
contract rather than a migration of `src/baton_work/authority.py`'s, and it
opens only the SQLite file its caller hands it.

The deployed executable `/home/sl/opt/baton/v11/8835cd5/bin/baton` is invoked as
an unmodified black-box CLI/JSON client. It is never copied and never patched.
Neither this prototype nor any model in it opens THAT executable's SQLite file
— nor any other v11 authority's. `src/authority/` opens the disposable v12
store its caller hands it and nothing else, which is a different file with a
different schema; the qualification is added here because the unqualified
sentence would now read as a claim this subtree no longer makes.
