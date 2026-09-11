# W71879 executable packaging — tuner141676

The operator's source/target and approved time limits are consumed. Concrete
packaging now lives in `prepared-141676/`: full task and policy documents,
retained image build context, image builder/byte checker, public Authority and
configuration generator, and one-submission CLI runner with a deadline guard.
No product source was changed. No image was built or selected, no runtime was
started, and the actual run remains held. This handoff supplies exact missing
grants for the existing operational decision; it does not ask for a new Work.

## Inputs and authority

The source and target at `/home/sl/.local/state/baton/v12/w71879-run1/{source,target}`
both match commit `2fbb2d456638e5706218020aebfa47f0a82c8920` and tree
`3492ba64448ab9d39bde53ee6456ce24e74ece2c`; target status is clean, and both
payloads match all ten prepared baseline files. See baseline-observation.json.
M141636 supplies wall1200s, implementation240s, review/judge180s, integration120s.
It explicitly corrects the missing numerical-allocation premise. Existing
preparation costs/uncertainty remain; no W103068 reserve transfers.

The exact fresh v12 Authority UUID is
`c71879ab000000000000000000000001`, with scope `scope:w71879-run1`.
Job A/B Works are `c71879ab-W1`/`c71879ab-W2`; the verification/review/approval
judge Works are `c71879ab-W3`/`c71879ab-W4`/`c71879ab-W5`. These are declared
bootstrap operands, not claims that production Works already exist.
`deployment.bootstrap` creates them through the public Authority API, with
distinct actors/principals, explicit routes and scoped verify/review/approve/
integrate grants. It performs no claim, receipt, publication or lifecycle step.
The actual bootstrap must match the validated policy generation and principals.

Five stage workers and three separate judges use the actual `operator-file` /
`w64268-run1` mapping in `/home/sl/.baton/credential-sources.json`. The registry
metadata confirms that mapping. No credential payload was read or copied.
Each actor has separate launch/credential roots; all share the configured
manager storage root. The actual tasks embed complete A/B behavior and path
scope. Judge tasks distinguish their own judgment from the coordinator's later
correlation, and do not demand unavailable original/peer report bodies.

The selected historical provider base is
`sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4`.
The retained overlay recipe recopies current worker/profile bytes onto that
base; the integration candidate uses the retained accepted Dockerfile.integration
with the same explicit base. Neither build runs a package installer or changes
provider selection per attempt. Builds use no-cache, pull=false and network=none.
The helper checks immutable IDs, UID/entrypoint and every copied module's bytes
through never-started inspection containers, then removes only those containers
it created. Build results are candidates, not automatic selection.

The workload uses Claude CLI's default model selection, as the accepted adapter
actually invokes it; no distinct-provider or distinct-model observation is
claimed. The accepted factory emits its fixed `provider-diverse` pool label;
that label does not establish model/vendor diversity for this same-installation
run. Distinct actors, principals and fresh contexts are the configured facts.
No provider flag or application change is smuggled into packaging.

## Resource and evidence behavior

Docker reports32 CPUs and32718819328 memory bytes; the source/target filesystem
reported723990093824 free bytes. Accepted runtime restrictions remain2 CPUs,
2GiB memory,512 pids and the existing private scratch bounds. Even the conservative
eight configured owners plus two helper slots fit20 CPUs/20GiB. The runner
rechecks that capacity,22GiB available memory and16GiB free storage before submit.
Each deployment declares512MiB workspace capacity; this is a free-space
preflight, not a disk quota. Retained-run storage is observed against16GiB.

`run.py` starts exactly one ordinary CLI submission and one ordinary serve using
`tools.stage_execution:factory`. It requires the independently accepted review
locator, exact config digests and reviewed helper/input hashes in
`execution-review.json`; that file has deliberately not been fabricated here.
Immutable configs/tasks stay under `prepared-141676/frozen-config/`; all mutable
Authority/control/Job/integration/workspace/launch/credential/evidence state
lives under the external run root. Immutable input paths are permitted in the
checkout; mutable state is not moved there to avoid an access grant.

The guard reads public Authority assignment events and read-only status, plus
Docker metadata/stats. It measures per-attempt limits from actual claim events,
including completed claims, and uses a POSIX alarm for the nearest observed
active-claim/global deadline. Integration's120s includes its active derived
judgment interval; the judge's own180s is not an extension of that integration
ceiling. On a deadline/failure it terminates its own serving process and stops
only runtimes bearing this fresh Authority UUID. Such a stop is exceptional
containment, never success or lifecycle repair, and its cleanup time is reported.
No automatic retry occurs. Sampling/storage observations are not filesystem
quotas or stronger resilience guarantees. H7 basic-status lag remains disclosed;
the guard never instantiates a serving factory to observe state.

The runner retains submit output, serving log, public claim/status snapshots,
runtime labels/IDs and Docker resource observations, both terminal stage sets,
whole-target final unittest output, total elapsed time and exceptional actions.
Final independent evidence assessment must still inspect actual original and
derived authorization/custody, unchanged original source and private bases,
both target changes, and honest terminal results. No completed stage label or
the guard's own result alone substitutes for that assessment. The source/target
initial observation is retained separately; production owners retain candidate,
target and integration histories. Fault C, forced correction, companion refusal
and stronger hardening remain deferred.

## Exact grants and operator operand

`prepared-141676/commands-and-grants.json` holds exact argv arrays, cwd and the
installed-rule check outputs for every command. Checks read both
`/home/sl/.codex/rules/default.rules` and `baton.rules`. The existing unconfigured
Job Manager status prefix matches allow. The configured serve prefix and the
three helpers below have **no matching rule**. That is not a claim that a
denied helper was run; no build/provision/run command was attempted. Local
prepare/validate succeeded inside current access, and render is likewise a
repository-only artifact operation after real image IDs exist.

All following Python commands use cwd `/home/sl/src/baton/v12/python`.
The narrow missing host grants are these exact commands, bound for review by
`prepared-141676/package-manifest.json`:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-141676/build_images.py
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-141676/deployment.py provision
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-141676/run.py
```

The first command needs engine build/create/cp/rm access for two retained
candidates and its own stopped inspection containers. The second needs
effective supplementary1001 and writes only this fresh run's declared external
roots through public APIs. The third needs that same host boundary and normal
engine lifecycle access for the reviewed CLI run, with only the stated
exceptional stop behavior. It launches the exact configured serve command as
its child; granting this reviewed runner does not require a second generic
Python, env, shell, Docker or blanket sandbox grant. No rule file was changed
and no escalation was requested by this managed context.

Slawomir also supplies the private bare Git workspace. The exact **operator-only**
command is:

```text
git init --bare /home/sl/.local/state/baton/v12/w71879-run1/integration-workspace
```

The agent has not run it. The provisioning script reads that repository's
type and refuses absence; it never initializes, commits or repairs Git.
Host processes already hold1001, so no host restart/group repair is requested.

## Existing continuation sequence

Review the prepared helpers/commands for the operational grant decision in this
same Work. Once the build grant is installed, tuner builds and checks the two
candidates, then runs `deployment.py render` within current repository access.
That produces full schema-valid frozen run inputs with real candidate image IDs;
no placeholder image is accepted as an actual build output. The existing
material-delta review binds those exact inputs and selects the checked images.
Tuner records the actual accepted image selection in selected-images.json,
provisions the fresh Authority once, and compares its actual public facts to
the reviewed plan. Review evidence and hashes populate execution-review.json
only after that review actually accepts; no synthetic runtime judgment is used.
The final run grant does not lift the review hold by itself.

After the existing access and review conditions are satisfied, tuner executes
run.py once, retains actual A/B evidence and passes for independent assessment.
If bootstrap/build fails, preserve partial state and report the exact failure;
neither helper overwrites/retries an existing run. This is continuation of
W71879, not a new planning Work or provider correction.

## Validation and cost

Public-schema/bootstrap validation passed after two packaging errors were
corrected: a31-character UUID literal and a tuple inside canonical JSON. The
current32-character UUID and arrays are explicit. A later AST check caught an
indentation error in the unexecuted deadline helper; it was corrected before
handoff. These are preparation errors, not Baton product findings. Local path
guesses for provider modules were resolved with rg; no required file remains
unreadable. See validation.json and spending.json for retained temporary paths,
exact measured validation costs and uncertainty.

Validation uses fresh temporary Authority stores through public APIs and emits
complete documents with the historical base image in both image slots. This
checks document/bootstrap composition only. Those temporary documents are
explicitly not the selected run configuration and are never submitted. No test
fixture provider, injected port, model judgment or lifecycle receipt was used.
No actual engine build/container/model or A/B execution occurred. No component
test suite was rerun; accepted provider evidence is reused within its scope.
