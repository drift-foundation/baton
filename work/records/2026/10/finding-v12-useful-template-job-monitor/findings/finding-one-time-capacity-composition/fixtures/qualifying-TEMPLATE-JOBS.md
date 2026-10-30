<!--
A VERIFICATION FIXTURE. NOT THE DELIVERABLE.

This file exists so `prove_guide_contract.py` can drive the selected guide's
verification contract to a real PASS, next to the real refusals. Writing
`v12/TEMPLATE-JOBS.md` is the Job's own work and this preparation does not do
it. Nothing in the composition the installer consumes refers to this file: it
is a test input, kept apart from the operational output on purpose.

It is deliberately thin. It satisfies the MECHANICAL contract -- ordered
sections, the exact template version, invocations this build's own parsers
accept -- and it would not satisfy the parent's five acceptance criteria,
which are the independent reviewer's judgment and not this command's.
-->

# Template Jobs

Creating and watching an ordinary v12 template Job on an installed deployment.
Every example below uses the template version
`baton.v12.job-template.implementation-review/1`.

```sh
DEST=/home/sl/baton-instances/useful-template-job-w366962
DISTRO=/home/sl/baton-instances/useful-template-job-w366962/distro
UUID=00000000000000000000000000000000
WORK=00000000-W1
ATTEMPT=attempt-1
```

```sh
"$DISTRO/baton-v12-stack" identity
```

## Creating the Job

```sh
"$DISTRO/baton-v12-stack" manager --store "$DEST/db/jobs.sqlite3" --incarnation operator-1 --authority-uuid "$UUID" create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" --task template-job-guide-42bed8bb --template baton.v12.job-template.implementation-review/1 --source installed --provider-turn-seconds 3600 --verification-command-seconds 900 --statement "Write a reusable operator guide." --acceptance "Examples use supported manager create with input-only operands." --work-scope v12/TEMPLATE-JOBS.md
```

## What the inputs mean

The task, statement, acceptance criteria and scope are inputs the manager
composes a submission from. `--source installed` selects the source the
installation bound; the template version selects the two-stage
implementation/review shape and its limits.

## Watching it without touching it

```sh
"$DISTRO/baton-v12-stack" start --instance "$DEST/instance.json"
"$DISTRO/baton-v12-stack" status --instance "$DEST/instance.json"
"$DISTRO/baton-v12-stack" monitor --instance "$DEST/instance.json" --interval 3 --ticks 400
```

Reading the status is a projection over a document this deployment already
wrote. It is not contact with a worker, and ending the monitor does not stop
scheduling.

## Independent review and the held result

```sh
"$DISTRO/baton-v12-stack" manager --store "$DEST/db/jobs.sqlite3" --incarnation operator-1 --authority-uuid "$UUID" status --control "$DEST/db/control.sqlite3"
"$DISTRO/baton-v12-stack" record read --authority-store "$DEST/db/authority.sqlite3" --authority-uuid "$UUID" --work "$WORK"
```

A completed implementation stage is not an accepted candidate. The review
stage reaches its own verdict and the result is held for a human.

## When an attempt fails

```sh
"$DISTRO/baton-v12-stack" attempt-diagnostics "$DEST/state/status.json"
"$DISTRO/baton-v12-stack" logs --logs "$DEST/state/launch/logs" --attempt "$ATTEMPT" locators
```

An exceptional stage is read, not silently retried.

## The human disposition

```sh
"$DISTRO/baton-v12-stack" disposition pending --authority-store "$DEST/db/authority.sqlite3" --authority-uuid "$UUID" --work "$WORK" --root "$DEST"
"$DISTRO/baton-v12-stack" stop --instance "$DEST/instance.json"
```

Approval is the owner's act. Stopping the deployment is not cleanup and is not
a disposition.
