# Credential-free Codex 0.169.0 tier recognition — unexecuted proposal

No engine command, Codex subprocess, credential access or provider call has been run for this packet. Existing N3/Stage A evidence stays retained; no Stage A rerun is requested. The offline discovery and a later configuration validation are separate from the one selected live invocation.

## What is known

Retained exact-build exec help documents `-c <key=value>`, TOML parsing, `--strict-config` and `--ignore-user-config`. It says strict mode rejects unrecognized fields in **config.toml**; it does not establish the treatment of command-line overrides. It says ignore-user-config skips CODEX_HOME/config.toml; it does not prove override precedence or that a particular key survives. Root help lists debug, doctor and app-server but their diagnostic subcommands/options have not been inventoried. No authoritative effective-config output or exact-build loader/source evidence is retained.

Thus neither help exit0, ordinary command exit0, a printed input string, absence of an error, nor a generated schema alone proves `service_tier="fast"` is active. Unknown keys might be ignored; help may bypass loading entirely. Recognition, effective requested configuration, and actual server-served tier are three distinct claims.

## Exact first phase proposed for selection

Image: retained N3 digest17d250b7… (full digest in offline.selection.json), exact version0.169.0, UID:GID1000:1000. Fresh `/var/tmp/baton-codex-tier-discovery-386092` outside all repositories. Network none, no credential mounts or inherited auth environment, private empty HOME/CODEX_HOME, read-only root, dropped capabilities, no-new-privileges,512MiB,1CPU,128pids,128MiB tmpfs. No pulls/builds/installs. No real provider turn, login/status, config mutation, remote-control or app-server startup command is included.

Before any execution: select the exact packet/settings/authorization, claim W385830, verify current ownership and absence of the named root/container. `authorization` is null in the proposal. Then:

```
<prepared-python> setup_offline.py offline.selection.json
<prepared-python> render_offline.py offline.selection.json
```

Execute the standalone vectors in offline.commands.json only after that selection. The renderer runs no command. One container runs version once, then these five **help-only** probes once:

```
codex debug --help
codex doctor --help
codex app-server --help
codex exec --ignore-user-config --strict-config -c 'service_tier="fast"' --help
codex exec --ignore-user-config --strict-config -c 'baton_unknown_service_tier_probe="sentinel"' --help
```

The last two are grammar/short-circuit controls, not recognition evidence. Every help probe is traced for file/connect operations in the credential-free home.10s per version/help command; stdout/stderr each1MiB (version4096bytes), trace16MiB per probe, no retries. Outer150s includes bounded process termination/drain. A bound stops remaining probes; no automatic continuation. Retain nonzero/help error outputs, do not substitute commands.

## Effective-config phase — command unresolved, do not guess or launch

Review the exact-build help first. Identify a documented read-only diagnostic which returns the **typed effective configuration after merge, validation and normalization**, including service_tier and preferably origin/precedence, without starting a turn. It must exercise the exec configuration path with --ignore-user-config, or be accompanied by exact-build authoritative source/control-flow evidence proving the loaders and override ordering are the same. A doctor/app-server config echo using a different loader is not sufficient. Do not infer a `config/read`, dump-config or debug command merely from its name in another version. No such command is enabled by this packet.

If that surface exists, return its exact argv/protocol for bounded offline selection with this matrix, each in a distinct empty home:

| Case | Required evidence |
|---|---|
| Omitted tier, --ignore-user-config | Typed effective baseline; do not call it Standard without evidence |
| `-c service_tier="fast"`, --ignore-user-config | Typed normalized field equals fast, sourced from command-line override |
| Invalid type/value for the same key | A field-specific validation error before any provider operation; this is recognition evidence, not proof fast works |
| Deliberately unknown control key under strict mode | Establish whether unknown overrides are rejected or silently ignored |
| Synthetic conflicting user config, with and without --ignore-user-config | Show the user file is excluded by the ignore option while the explicit command-line fast value remains effective |

Do not treat acceptance of both the real and unknown key as recognition. If the effective dump is an untyped merged map that retains arbitrary keys, it cannot establish normalization/recognition. If a schema is available, pin it to the exact image/build and loader and combine it with actual typed post-load evidence; a key in a schema alone does not show the invocation used it. Invalid-key rejection alone proves only that negative path; no success fixture may be invented.

If the exact build has no safe diagnostic, **retain uncertainty** and keep fast execution gated; obtaining a supported exact-build source/loader proof is a separate bounded preparation question. Never run an exec prompt or contact a provider merely to make the offline check appear conclusive. No programmatic success classifier in this packet claims recognition: conclusions.json always leaves recognition/effective config/served tier unproved.

## Evidence and cleanup

Retain frozen selection/packet and image identity, exact version and argv, all bounded stdout/stderr/exit/duration records, tool inventory, file/connect traces, before/after-every-phase home metadata, container inspect/OOM/error/mount/user/network records and wall-clock bounds. No bearer material is present; inspect output before publication anyway and retain unexpected data privately. A zero connect trace applies only to the probed path.

On timeout stop only the named container with15s grace, inspect, kill only if still running, wait/inspect until cessation is positive. Remove only after confirmed exit; retain the no-such-object response and empty run-label query. No retry or broad cleanup. Preserve image, source, evidence and private home until classification; no protected Git metadata cleanup. If cessation cannot be established, retain the gate and report the exact runtime uncertainty.
