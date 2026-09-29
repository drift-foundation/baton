# Inspecting a first v12 Job

A single useful Job is an intermediate result. It does not establish independent
parallel adoption, and provider completion does not establish accepted retained
output. The retained proposal needs independent review of its exact bytes.

Before a task starts, the host validates its contract, profile, inputs and resource
policy, reserves capacity, and settles the current claim. The host may prepare a
fresh private attempt under exclusive ownership: allocate directories, publish
inputs and task files, and set initial permissions. It must durably record
completion, prove no preparation writer remains, and recheck resource identity
before admitting and launching the task. External I/O stays outside database
transactions. An expired deadline or empty local map is not proof that a writer
stopped or that a root can be reused.

Use the configured status surface to correlate the Job, attempt and exact runtime.
Treat the timestamp and observation freshness as part of the answer. An old
snapshot reports previously recorded state; missing or stale observation means
unknown, not zero running attempts. A restart reconciles durable identities and
permission instead of redispatching because its local memory is empty.

Stopping a stack supervisor is not stopping a task runtime. Confirm that the exact
producer and all relevant writers stopped, and retain unresolved ownership or
cleanup holds when that cannot be proved. Do not infer successful collection from
a provider response, process exit, missing runtime visibility or an empty status.

Inspect logs through the supported file-only commands. Obtain the launch-home and
attempt identity from the correlated deployment evidence; the examples below use
placeholders that must be replaced with those exact values.

```sh
baton-v12-stack logs --logs <launch-home>/logs --attempt <attempt-id> locators
baton-v12-stack logs --logs <launch-home>/logs --attempt <attempt-id> read --stream provider.stderr
baton-v12-stack logs --logs <launch-home>/logs --attempt <attempt-id> read --stream worker.stderr
```

The `--logs` and `--attempt` operands precede `locators`, `read` or `follow`.
Read the capture state and declaration: missing output is not empty output, and an
unreadable declaration does not establish what the writer captured. These log
commands read files; they do not inspect coordination stores or start a runtime.

The configured shared UID/GID arrangement must provide required host access. If
status or collection reports a permission error, retain the exact operation and
path and preserve the workspace. Do not normalize permissions, run a helper,
chmod/chown files, reset the workspace, or report collection as successful.
Accessible output can progress without a normalization receipt. Result identity,
producer cessation and independent acceptance still matter on that path.
