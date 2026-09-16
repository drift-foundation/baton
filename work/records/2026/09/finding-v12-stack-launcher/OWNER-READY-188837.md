# W183883 — owner execution packet for the accepted implementation

Prepared by baton.codex under claim188837. Read with
OWNER-STANDALONE-INTERFACE-20260916.md. Implementation R1–R4 corrections are
accepted; product guide alignment is the remaining delivery edit. This packet
supersedes manual clone prerequisites in OPERATOR-INDEPENDENT-REPOSITORY.md as
an execution recipe. That older document remains historical evidence.

## Supply the actual deployment inputs

Use a complete bootstrap input document, retaining already selected identities,
profiles, images, capabilities and credential REFERENCES. Do not copy fixture
bases/credentials or retained proof paths into production. The remaining choices
are the source repository, full immutable base for each Job, import reference,
integration observer, and a fresh absolute destination outside the source tree.

**SUPERSEDED under claim189383 by OWNER-VERSION-STAMP-20260916.md, and the
correction is recorded here rather than left in the packet's original wording.**
`repository_source` is no longer an input member: a document that still carries
it is REFUSED by name with the reason. The source is inferred from the
repository containing this distribution's `v12/justfile` -- the checkout the
bootstrap runs from -- so the two-operand command prepares the repositories by
default, and no source is communicated in deployed JSON.

Bootstrap prepares independent non-local clones under the destination:
`repo/target.git`, `repo/workspace`, `repo/source-<worker_id>`. Do not
pre-clone. Omit target/workspace/nominated-source overrides to use these derived
paths, or supply those exact compatible paths; explicit mismatches are refused.

To install from another checkout, or to install none, the options go in the
FOURTH operand after an empty third -- `just` binds bare positionals in order
and the recipe refuses an option written in a positional slot:

```sh
just bootstrap /absolute/inputs.json /absolute/new-destination "" "--no-repositories"
just bootstrap /absolute/inputs.json /absolute/new-destination "" "--repository-source /other/checkout"
```

Select `integration_target_reference` and `integration_observer`; each Job's
`line_declared_base` is a real full immutable revision, not a fixture placeholder.
The bootstrap proves repository identity independence, no borrowed objects and
presence of declared bases/reference in the prepared target. Worker
`workspace_storage` is derived under the destination when omitted; any explicit
path must resolve inside it. Valid sharing within one destination is retained.
Credential registry references remain owner-selected; their secret contents are
not copied into this packet or deployment evidence.

With `--no-repositories`, repository preparation is omitted and reported.
This supports existing explicit-input/idle-runtime cases; it does not establish
that a complete production integration is ready. Keep that distinction in output.

## Owner-run command

These are parameterized commands; replace the paths with the actual selections.
The source checkout's prepared build environment must exist (`just setup` is the
separate one-time prerequisite documented in v12/STACK.md).

```sh
cd /path/to/baton/v12
just bootstrap /absolute/inputs.json /absolute/new-destination
```

The two-argument command builds current source, prepares the selected repositories
and deployment, and writes destination-local justfile/instance.json. An explicit
third prebuilt-distro operand is an optional development form. The retained188671
bundle predates the final failure corrections and is not the final build to
select for this owner run. Agents do not perform the Git mutations; the owner
invokes the completed operation.

```sh
cd /absolute/new-destination
just status
just repository
```

For the selected idle lifecycle check, use destination-local `just start`,
`just status`, `just monitor`, `just stop`. From another directory:

```sh
just --justfile /absolute/new-destination/justfile status
```

A source-checkout wrapper takes the DESTINATION DIRECTORY, for example
`just status /absolute/new-destination`, not its instance.json. Only the low-level
bundled command takes `--instance /absolute/new-destination/instance.json`.

## What the built command now reports

The bundle carries its own version and build provenance, captured when it was
packaged:

```sh
/absolute/new-destination/distro/baton-v12-stack --version
baton 12.0.0 (3c0dd082, dirty)
```

Dirty builds are allowed; the commit identifies the BASE the build was made
from, and the artifact manifest identifies the bytes. A clone carries commits,
so uncommitted work in the checkout does not reach the prepared repositories --
named, not changed.

## Return evidence

Return the non-secret selected source/base/reference/observer and destination,
input/configuration path mapping, bootstrap transcript, repository report and
runtime identity/manifest reference. Record idle lifecycle outputs if run. Do not
label repository-layout reporting alone as immutable-base validation; preserve
the bootstrap's actual checks. No live Job/provider/engine qualification or v11
cutover is selected by this packet. W183883 remains open until the owner step is
resolved; W177936 remains parked and v11 remains authority.
