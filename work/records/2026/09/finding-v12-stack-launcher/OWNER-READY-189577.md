# W183883 — current owner execution packet

Prepared by baton.codex, claim189577. Implementation, version/stamp, guide and
focused test corrections are independently accepted. Read with
OWNER-STANDALONE-INTERFACE-20260916.md and OWNER-VERSION-STAMP-20260916.md.
This packet supersedes earlier packets as the current execution recipe; retain
them as history. No manual pre-clone or additional planning gate is required.

## Actual selections

Use the real complete bootstrap inputs, retaining selected identities, profiles,
images, capabilities and external credential REFERENCES. Supply each Job's full
immutable line_declared_base, integration_target_reference, integration_observer
and a fresh absolute destination outside the checkout. Do not substitute fixture
bases or copy secret contents into inputs/evidence.

The default source is the repository containing this distribution's v12/justfile,
inferred independently of the caller's cwd. Do not include repository_source in
JSON: it is now refused. The owner command prepares independent --no-local clones
at repo/target.git, repo/workspace and repo/source-<worker_id> under destination.
Omit target/workspace/nominated_source overrides to derive those paths, or supply
the compatible exact paths. Bootstrap verifies repository independence, object
store isolation and presence of every declared base/reference. Worker storage is
derived under destination when absent; explicit paths must resolve within it,
with valid sharing inside this destination preserved. Credentials stay external.

Dirty application builds are allowed and report their captured base commit and
dirty state. Repository clones contain committed content; uncommitted application
changes are not copied into the prepared repositories. No different copying
policy is selected here. Application version is separate from each Job's base.

## Owner command

Run from the intended source checkout, after the separate one-time `just setup`
prerequisite has prepared the build environment:

```sh
cd /path/to/baton/v12
just bootstrap /absolute/inputs.json /absolute/new-destination
```

This builds current reviewed source, prepares independent repositories and stores,
and emits the destination-local justfile and selector. The owner performs this
operation because it includes Git mutations; agents do not clone repositories.
Do not select a retained proof bundle as a substitute for the current build.

Optional development overrides use the fourth positional argument after empty
DISTRO (these examples use absolute source paths without spaces):

```sh
just bootstrap /absolute/inputs.json /absolute/new-destination "" "--repository-source /absolute/other-checkout"
just bootstrap /absolute/inputs.json /absolute/new-destination "" "--no-repositories"
```

The latter intentionally omits repository preparation and establishes only the
selected explicit-input/idle case, not production integration readiness. The
normal production command is the two-operand command above.

## Inspect and return evidence

```sh
cd /absolute/new-destination
./distro/baton-v12-stack --version
just identity
just repository
just status
```

For the selected idle lifecycle check, use destination-local `just start`,
`just status`, `just monitor`, `just stop`. From elsewhere use
`just --justfile /absolute/new-destination/justfile status`. A checkout lifecycle
wrapper takes the destination directory, not instance.json. Only the low-level
bundle command takes --instance.

Return nonsecret source/base/reference/observer/destination selections, input and
emitted-configuration mapping, bootstrap transcript, repository report, version,
identity/manifest and selected lifecycle outputs. Repository layout reporting is
not a substitute for the bootstrap's immutable-base checks. No Job/provider/engine
qualification or v11 cutover is selected. W183883 stays open until owner execution
or explicit resolution, W177936 stays parked, and v11 remains coordination authority.

## Retained artifact history

The current proof build has81 files and digest
81d45b33e6009ff623737e1c330c4c4d3e662fa6811f781a13d5558fabdc6270.
The retained189383 install at /var/tmp/w183883-version-189383/deployment has81
files and digest32b81cd3b46149bbc90ca6116f56b2e9540d789b1a5b989600098f12be63a38a;
its stamp predates the final capture corrections. The independent review confirmed
both remain unchanged through the focused test run. These are distinct artifacts;
the owner two-operand bootstrap builds current source. Prior unavailable external
disk-backed bootstrap fixtures remain a coverage limit; actual production
repository preparation is still pending owner execution.
