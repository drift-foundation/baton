# Q4 executable packet q4-386227 — Codex implementation → Claude review, offline first

Prepared 2026-11-25 by K (`baton.prompt`, interactive copilot, no claim) on owner request, from `../q4-preparation-386225/OWNER-SELECTIONS.md`. Nothing was executed against a real engine, credential or provider. No product path, DESIGN or protected Git edit. `../q4-preparation-386225/` is unchanged; this packet supersedes the command templates in its `PATH.md`.

Payload manifest (`payload.json`): `1eb7ff182c623dfecfe1fed97b9176da441f80e13da2b7b007b1b85c6d3097dd`. Commands: `COMMANDS.md`. Check outputs: `checks/`.

## What it runs

One script, `owner-run.py`, with two separately selected phases.

| Phase | Does | Never does |
| --- | --- | --- |
| `--offline` (A) | Confirms the accepted Codex image `2c982530`; builds one Claude image from frozen `b5abf798` (base pinned by digest, `--no-cache`); inventories it offline (version, help flags, every `/opt/baton` file hash against source); creates a disposable fixture repository; writes a private registry; installs a fresh instance; composes the Codex implementation worker and the Claude review worker; configures uncertainty routing to `baton.slaw`; composes the serving object once with no Job. | Start a worker container, open a login, call a provider. |
| `--live` (B) | Creates one Job (implementation then review, nothing else); serves it in this process; stops at a recorded verdict, an uncertainty owner item, a held review, a failed stage, or the bound; proves cessation and removal; withdraws delivered credentials; verifies the edit from the reviewed line after cessation. | Retry, run a correction round, run integration, start a third container. |

## Owner selections, as bound in the script

- Claude: request `claude-fable-5[1m]`, require reported identity `claude-fable-5`, CLI 2.1.247.
- Claude credential: `operator-file:claude-primary-subscription` → `/home/sl/.claude/.credentials.json`, delivered read-only. The historical alias appears nowhere in this packet.
- Codex: unchanged (gpt-6-astra, `codex-pushcoin-subscription`, image `2c982530`).
- Posture: bridge network, uid:gid 1000:1000, read-only root (asserted on each real container while it exists).
- Limits: 600 s per provider turn, 15 s verification, one container per role in a fixed image order.
- 20-minute overall bound, enforced by the script: an alarm at 1200 s, a loop deadline at 1170 s, and the same deadline on every engine command; cleanup then has 150 s.
- Uncertainty: routing reviewer `qualification.claude`, recipient `baton.slaw`; the owner queue is read at the end of the run. No extra uncertainty run.

## Credential source configuration

- The packet writes its **own private registry** at `/var/tmp/baton-q4-386227/credential-sources.json` in the supported `baton.user-credential-sources/1` format, with the two references and their paths. It holds no secret.
- Your ordinary registry and every existing deployment's configuration are not read, written or referenced. Nothing can be overwritten there.
- `registry.py` enforces the conflict rules (same pair, different path → refused, nothing changed; ambiguous or non-private registry → refused). It never opens a login file. Adding the alias to your ordinary registry is an optional separate act in `COMMANDS.md`.
- The login files are opened only by the manager, only in `--live`. Before any provider turn the script checks their metadata (private ordinary file, within the delivery bound) so an unusable source fails before the Codex turn is spent.

## Existing deployments are preserved

Fresh private root, own Authority and stores, no shared stack state directory, no supervisor processes. Containers are removed only by exact name after a label check; no prune; no image is removed. `/home/sl/baton-instances/*` and `~/.baton` are never touched.

## Three product gaps found in the dry run, and how the packet handles them

All three would have stopped the command templates in the earlier `PATH.md`. They were found without any build.

1. Two workers with different images cannot share one launch home once both select a verifier layout (the second selection is refused as "a different verifier-layout selection is already delivered"). `pool compose-worker` gives every worker the same launch home. The packet gives the review worker its own launch home; nothing else in its composed document changes.
2. Under the default template `/1` the review worker declares only `proposal`, and the review adapter refuses ("declares no findings, logs"). The packet composes both workers and creates the Job under `/3`, whose role contract declares the review outputs.
3. A source-run instance has no target repository unless the installer prepares it, and the installer form requires a built runtime bundle. The packet calls the installer's own repository and composition steps directly from the frozen source; no bundle is built.

Each is a candidate product follow-up; none is changed here.

## Deterministic proof (`checks/`)

Real `offline()` and `live()` run end to end: the product's bootstrap, pool composition, Job creation, Authority, stores, stage-execution composition, OCI vectors and review driver are real. Docker is substituted at `subprocess.Popen`; the two providers are simulated at their process seam with labelled synthetic output; logins are synthetic. An audit hook fails any check that opens either real login path or your ordinary registry.

| Scenario | Result |
| --- | --- |
| `offline-pass` | Passes: one build, three inventory runs, no worker container, two workers, routing read back from the Authority, private registry 0600. |
| `build-fail`, `wrong-version`, `image-drift` | Offline fails, exit 1, no instance configured. |
| `accepted` | Codex stage completed with custody; the reviewer was given the checkpoint containing `after` + newline; Claude attribution matched with the selected identity plus an extra contributor; verdict `accepted` recorded by the manager; two containers, both removed; credentials withdrawn; edit verified from the line. |
| `uncertain` | No verdict; one owner item addressed to `baton.slaw`; review not completed; held container removed by the script. |
| `wrong-contributor`, `no-report` | Review held, no verdict, no owner item. |
| `no-edit` | Implementation fails its verification; the review never starts. |
| `launch-fail` | Fails before any provider; exit 1. |
| `stall` | With the bound shortened to 42 s, the run ends as `wall-bound` and cleans up. |
| `oversize-claude-login` | Refused before any container. |
| `check_registry.py` (11 cases), `check_observe.py` (30 cases) | Pass. |

Every live scenario ends with `acceptance: held-for-private-evidence-review` and `native_job_success: false`.

## What the simulation cannot show

- Real Docker behaviour: the Claude build itself (needs the pinned node base present locally, as for Q1, and network for the package install); whether `claude --version` and `--help` run under a read-only root with a small `/tmp`; the worker's in-container mount proof for the Claude image.
- Whether the real CLI accepts the selector and reports the identity. That is what the live turn answers.
- A real Claude login file larger than 4096 bytes is refused by the manager's delivery bound; the script checks this before the Codex turn.

## Risks to know before selecting B

- The Claude login is your live Claude Code login, delivered read-only. If the CLI refreshes its token during the turn, the copy on disk is not updated and the host login may need re-authentication. Refresh behaviour under read-only delivery is unqualified. The run is short; starting it soon after a fresh login lowers the chance.
- Template `/3` lets the implementer ask the reviewer a question. That would need a third container, which the runner refuses; the run would end as an error, cleaned up, with no verdict.
- An uncertain or held review exits 0: the capture worked and the outcome is held. There is no owner continuation command; the instance is simply left stopped.

## Handoff

- Next: review of this packet; then owner selection A; review of `OFFLINE-RESULT.json`; then owner selection B; then a separately authorized private-evidence review.
- I authored this packet and do not review it.
