# Supported command forms — W376804

Preparation examples only; none were executed against an instance. Eight vectors
were checked against the exact committed parsers with execution intercepted
immediately after parse_args. This is syntax evidence, not installation, admission
or runtime evidence. Selected source and limitations: READINESS-377930.md.

## One-time host artifact preparation

The exact diagnostic source export is /tmp/w376804-8876bf95-6mw5zvec, bound by
CHECK-377930.json. Its source files must still match all recorded hashes before a
build. The supported recipe, **for separate owner build selection only**, is:

```sh
just --justfile /tmp/w376804-8876bf95-6mw5zvec/v12/justfile build /tmp/w376804-8876bf95-6mw5zvec/host-build
```

This builds the host, not Docker. It can install locked build dependencies into
the prepared environment. Prerequisite is the supported Python environment from
`just setup`; none was provisioned here. Propose a 900s build timeout with retained
partial output and no automatic retry. The export has no .git, so build identity
may honestly report unknown Git provenance: pair its measured artifact inventory
and identity with CHECK's exact source hashes; never edit the stamp to claim a
commit. Bind the entire one-folder distribution, its interpreter/dependencies,
platform, identity and hash inventory for independent review, not only the entry
binary. No artifact digest exists until that build occurs.

**Recommendation is to wait for the accepted bounded installer corrections before
selecting the deployment build**, then explicitly revise the source manifest and
command operand to that frozen candidate. The diagnostic 8876bf95 build above
cannot fix installation safety. There is consequently no safe bootstrap/install
command recommended for this candidate; this is the specific unsupported next
operation, not missing permission to finish preparation. The supported generic
form is `just bootstrap INPUTS DESTINATION DISTRO` (STACK), but filling INPUTS
with a simulated fixture would not create the missing qualified deployment.

## Routine input-only creation after qualified installation

The installer must supply the selector, registered workers and qualified role
configuration once. The proposed destination is not created or reserved. Read
AUTHORITY_UUID from that installation's authority-identity.json through its
supported output; do not use CHECK's parser-only zero UUID. UUID, stores and
instance paths are redundant CLI requirements at this source, not per-Job
operator-authored manifests. W375518 owns the improved instance-selected surface.

```sh
DEST=/home/sl/baton-instances/useful-template-job-w376804
STACK=/home/sl/baton-instances/useful-template-job-w376804/distro/baton-v12-stack
"$STACK" identity
```

After actual installation/role qualification, and with its manager idle, the
existing /1 creation syntax for the complete selected task is:

```sh
"$STACK" manager --store /home/sl/baton-instances/useful-template-job-w376804/db/jobs.sqlite3 --incarnation w376804-create-1 --authority-uuid "$AUTHORITY_UUID" create --instance /home/sl/baton-instances/useful-template-job-w376804 --control /home/sl/baton-instances/useful-template-job-w376804/db/control.sqlite3 --authority /home/sl/baton-instances/useful-template-job-w376804/db/authority.sqlite3 --task template-job-guide-w376804 --statement 'Write a reusable operator guide for ordinary v12 template Job creation and observation using the supported installed command. Explain the supplied task, source, scope and acceptance inputs, template version and limits, independent review and held results, failure/recovery boundary and human disposition. Verify all documented command examples against current supported parsers and behavior. Preserve the historical instance4 QUICKSTART facts; do not claim source features are installed there. Deliver documentation, not product redesign.' --template baton.v12.job-template.implementation-review/1 --source installed --work-scope v12/TEMPLATE-JOBS.md --job-id template-guide-w376804 --submission-id template-guide-w376804-1 --provider-turn-seconds 3600 --verification-command-seconds 900 --acceptance 'Examples use supported manager create with input-only operands and the exact template version; they do not author admission manifests or replace owner APIs.' --acceptance 'Source/installed distinction, actual deployment identities, proposed versus executed operations and default/overridden limits remain explicit and truthful.' --acceptance 'Monitoring is read-only; query time is not worker contact; unknown activity is not success; ending the monitor does not stop scheduling.' --acceptance 'Implementation completion, independent verdict, held proposal, human acceptance and Git integration are distinguished. Failure/retry and runtime-cessation prerequisites are stated without silently retrying or claiming stop is cleanup.' --acceptance 'Semantic evidence checks command order/options and statements against owning implementations, not only headings/byte count. Review binds the actual candidate.'
```

This command is conditional documentation, not authorization. `--task` is a task
identifier, not a filename. The one-time role deployment must already provide
TASK-377930.json's verification contract and immutable installed source. No user
must reseal manifests for each routine Job. If changing ordinary input requires
that, report it to W371075 instead of adding an agent preparation step. Reusing
a submission ID with changed inputs is not retry authority. No fixture UUID,
source archive or model-generated receipt substitutes for installation.

The supported subsequent `start` below starts supervisors and can dispatch the
created Job; it therefore needs explicit run selection. Current /1 requires
create-before-start. Routine stop/create/start is not the owner-selected permanent
workflow and does not satisfy create-while-serving or the whole-path 60s bound.

```sh
"$STACK" start --instance "$DEST/instance.json"
```

## Observation and retained evidence

Read-only views once the actual instance exists:

```sh
"$STACK" status --instance "$DEST/instance.json"
"$STACK" monitor --instance "$DEST/instance.json" --interval 3 --ticks 1
"$STACK" view --status "$DEST/state/status.json" --job template-guide-w376804
"$STACK" attempt-diagnostics "$DEST/state/status.json"
```

Take ATTEMPT_ID from that Job view's exact attempt field, not its task, Work,
allocation or image identity. Supported log forms (no engine or store access):

```sh
"$STACK" logs --logs "$DEST/state/launch/logs" --attempt "$ATTEMPT_ID" locators
"$STACK" logs --logs "$DEST/state/launch/logs" --attempt "$ATTEMPT_ID" read --stream provider.stderr --text --from-byte 0 --limit 4096
```

Provider stderr may contain sensitive task/provider material; retained logs are
not public protocol diagnostics. Missing output is not an empty successful stream.
The snapshot is not an engine observation or a qualification receipt. Measure
whole-path startup from received task/inputs to attributable substantive activity,
not first monitor query or command receipt.

## Separate supervisor stop and stopped-failure settlement

No installed assignment-cancel command was found. See READINESS's concrete gap
and required exact-runtime cessation/launch-accounting action. The following only
stops owned supervisors; it must not be mistaken for stopping worker containers:

```sh
"$STACK" stop --instance "$DEST/instance.json"
```

After exact failed runtime cessation and offline instance ownership are established,
choose STAGE_ID and EPISODE from the actual Job status and an original stable
SETTLEMENT_OPERATION_ID for that episode. Do not substitute parser test episode1.
The supported preview command is:

```sh
"$STACK" manager settlement-preview --instance "$DEST/instance.json" --job template-guide-w376804 --stage "$STAGE_ID" --episode "$EPISODE" --operation-id "$SETTLEMENT_OPERATION_ID"
```

Preview returns a `request` object. Save exactly that object as request.json and
check package/deployment, assignment, full runtime, resource generation and faulted
exchange bindings before separate selection. This manual extraction is the current
command UX; automatic routine recovery remains an owner-delivered requirement,
not a service for an agent to perform for every failed Job. Then:

```sh
"$STACK" manager settle-stopped --instance "$DEST/instance.json" --document request.json
"$STACK" manager settlement-status --instance "$DEST/instance.json" --document request.json
```

Neither performs cleanup or creates acceptance. Unknown runtime/writer/launch
state keeps the hold. Exact request replay only continues the same selected
settlement; it never authorizes a new provider invocation. Retain the request,
responses, selector, package identity, configuration, task, stores, logs and
private outputs. There is no deletion or fresh-attempt command in this selection.
