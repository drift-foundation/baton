# W183883 — reviewed fresh-instance delivery

Prepared by baton.codex under claim190454 after independent review
review-2026-09-17T00-17-18Z.md. OWNER-FRESH-INSTALL-20260916.md governs.
This packet replaces OWNER-READY-189577.md and its mandatory Job-input gate.
That older packet remains historical evidence only.

## Result ready to review

Bootstrap installs an empty instance with its own generated, persisted Authority
identity. No Job, Work, declared base, target identity, worker assignment or
credential selection is required for that empty state. Real idle manager/publisher
and read-only monitor work; unconfigured work is refused at startup and on ordinary
ticks. Destination-local lifecycle remains independent of the source environment.

Use the complete JSON in `v12/STACK.md`, **A fresh installation has zero Jobs**.
It names only instance policy/profile/receipt settings. `state_root` in that
document is replaced by the chosen destination when installing. Do not add
`authority_uuid` or `repository_source` to JSON; the helper derives them.

## Owner operations

After the separately prepared build environment (`just setup`), run from the
intended checkout's v12 directory:

```sh
just bootstrap /absolute/instance-inputs.json /absolute/fresh-destination
```

This builds source, installs runtime/stores/configuration/justfile, and prepares
independent repositories from the checkout containing v12/justfile. No manual
pre-clone is needed. Slawomir owns actual Git operations and any commits; the agent
has made no Git mutations. Dirty builds report their base and dirty status, while
repository clones contain committed content.

The optional no-repository form is:

```sh
just bootstrap /absolute/instance-inputs.json /absolute/fresh-destination "" "--no-repositories"
```

Operate from the installed destination:

```sh
./distro/baton-v12-stack --version
just identity
just repository
just start
just status
just monitor
just stop
just status
```

`just monitor` is interactive; leave it with Ctrl-C. For a bounded evidence capture:

```sh
./distro/baton-v12-stack monitor --instance /absolute/fresh-destination/instance.json --interval 1 --ticks 2
```

The installed runtime is prepared once. Later configuration uses the guide's
stop/one-operand-bootstrap/start sequence and explicitly carries effective
target/workspace and worker storage/source values from deployment.json. Missing
existing selections are refused; repeating the two-operand installer does not
upgrade an existing runtime. No dynamic onboarding is selected.

## Evidence available and disposition

REVIEW-CANDIDATE-190454.json binds all 24 reviewed delivery paths.
Current bundle:81 files, digest
`f675e883ad0e752c1d2881702d9d6b40189e2f565bc21242268cd05abfe99911`,
version `baton 12.0.0 (fb5d39d6, dirty)`. FROZEN-LIFECYCLE-190149.json records the
author's actual no-repository installed lifecycle; reviewer independently verified
bundle bytes/version and13 focused checks. Earlier bundles are historical.
The detailed review preserves failed harness attempts and unknown costs.

Owner review/Git disposition is next. If selecting an owner installation, retain
bootstrap/version/manifest/repository report and lifecycle outputs for resolution
of this Work. No live Job/provider/engine qualification or v11 cutover is selected.
W183883 remains open until owner execution or explicit resolution, W177936 stays
parked, and v11 remains authoritative.
