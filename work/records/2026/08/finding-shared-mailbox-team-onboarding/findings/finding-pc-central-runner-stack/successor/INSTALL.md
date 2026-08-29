# Operator cutover — Pushcoin central-stack pilot

These steps are intentionally operator-owned. They install the reviewed files
only after Baton dispatch is paused and the shared lifecycle stack is stopped.
Generation 2 is already accepted; this cutover does **not** run `regen`.

The initial cutover and smoke have now completed. That smoke found two missing
reproducibility gates: the isolated `pc.code` Claude profile must be
authenticated before start, and the ACP child must receive exact Baton
locators in its environment. The main procedure below is correct for a fresh
install; an already-installed stack uses the bounded reconciliation in
[section 7](#7-reconcile-an-already-installed-stack).

The source directory used below is:

```text
/home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor
```

## 1. Revalidate the staged set and live baseline

Run both read-only verifiers, then, for an initial cutover only, ensure the live
inputs have not changed since the successor was prepared:

```bash
python3 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/verify.py
node /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/verify.mjs
sha256sum -c /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/SOURCE-SHA256SUMS
```

Stop if any check fails. A changed source input requires a fresh rebase and
review of this successor set.

`SOURCE-SHA256SUMS` pins the pre-cutover inputs. It is expected to fail after
the successor has been installed and must not be used as an after-install
integrity check; use the byte comparisons below or section 7 instead.

The verifier also requires `pushcoin-AGENTS.md` to name protocol 11, all five
accepted `pc.*` identities, and permanent `work/records/...` dossiers. Retired
protocol-10 command syntax may appear only in the explicit retirement notice;
no retired identity or active instruction may remain.

## 2. Drain and stop at the explicit boundary

```bash
python3 /home/sl/src/baton/tools/infra.py drain /home/sl/baton-v11.14aecfb --reason "install reviewed W10198 Pushcoin runner successors"
python3 /home/sl/src/baton/tools/infra.py dispatch /home/sl/baton-v11.14aecfb
python3 /home/sl/src/baton/tools/infra.py stop-drained /home/sl/baton-v11.14aecfb
```

Repeat the `dispatch` read until it reports `paused`; `stop-drained` refuses
without that state and signals no service on refusal.

## 3. Back up and install the literal successors

Back up the two replaced lifecycle inputs, execution policy, and Pushcoin
repository policy while the stack is stopped:

```bash
install -m 600 /home/sl/baton-v11.14aecfb/infra.json /home/sl/baton-v11.14aecfb/infra.json.pre-pc-W10198
install -m 600 /home/sl/baton-v11.14aecfb/codex-event-bridge.template.json /home/sl/baton-v11.14aecfb/codex-event-bridge.template.json.pre-pc-W10198
install -m 600 /home/sl/.codex/rules/baton.rules /home/sl/.codex/rules/baton.rules.pre-pc-W10198
install -m 600 /home/sl/src/pushcoin/AGENTS.md /home/sl/baton-v11.14aecfb/pushcoin-AGENTS.md.pre-pc-W10198
if test -e /home/sl/.config/baton/acp/pc.code/policy/launch-agent-sandboxed.sh; then install -m 700 /home/sl/.config/baton/acp/pc.code/policy/launch-agent-sandboxed.sh /home/sl/baton-v11.14aecfb/launch-agent-sandboxed.sh.pre-domain-W28681; fi
```

Install and byte-verify the durable Pushcoin policy before any new context or
agent can start:

```bash
install -m 664 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pushcoin-AGENTS.md /home/sl/src/pushcoin/AGENTS.md
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pushcoin-AGENTS.md /home/sl/src/pushcoin/AGENTS.md
```

Install the participant-local Claude policy before installing the manifest that
references it:

```bash
install -d -m 700 /home/sl/.config/baton/acp/pc.code/policy/claude
install -d -m 700 /home/sl/.local/state/acp-baton-bridge/pc.code/claude
install -m 600 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/claude/settings.json /home/sl/.config/baton/acp/pc.code/policy/claude/settings.json
install -m 600 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/claude/settings.json /home/sl/.local/state/acp-baton-bridge/pc.code/claude/settings.json
install -m 700 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/block-git-commit.sh /home/sl/.config/baton/acp/pc.code/policy/block-git-commit.sh
install -m 600 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/git_guard.py /home/sl/.config/baton/acp/pc.code/policy/git_guard.py
install -m 700 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/launch-agent-sandboxed.sh /home/sl/.config/baton/acp/pc.code/policy/launch-agent-sandboxed.sh
install -m 600 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/protected-paths.txt /home/sl/.config/baton/acp/pc.code/policy/protected-paths.txt
install -m 700 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/preflight-process-domain.sh /home/sl/.config/baton/acp/pc.code/policy/preflight-process-domain.sh
```

Provision the deployment-owned credential into the isolated profile without
printing it. Preserve an existing non-empty isolated credential because the
agent may have rotated it; copy the operator's authenticated Claude credential
only when the isolated profile is empty or absent:

```bash
test -s /home/sl/.claude/.credentials.json
if ! test -s /home/sl/.local/state/acp-baton-bridge/pc.code/claude/.credentials.json; then install -m 600 /home/sl/.claude/.credentials.json /home/sl/.local/state/acp-baton-bridge/pc.code/claude/.credentials.json; fi
test -s /home/sl/.local/state/acp-baton-bridge/pc.code/claude/.credentials.json
test "$(stat -c %a /home/sl/.local/state/acp-baton-bridge/pc.code/claude/.credentials.json)" = 600
```

If the ACP runtime still reports `cause=credential`, keep dispatch paused,
authenticate the operator profile through the provider's normal login flow,
stop the stack, and deliberately refresh the isolated copy with `install -m
600`. Never put credential contents in this repository, lifecycle JSON, logs,
or Baton messages.

Install the four lifecycle/dispatcher inputs:

```bash
install -m 600 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/acp-pc-code.template.json /home/sl/baton-v11.14aecfb/acp-pc-code.template.json
install -m 600 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/codex-event-bridge.template.json /home/sl/baton-v11.14aecfb/codex-event-bridge.template.json
install -m 600 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/baton.rules /home/sl/.codex/rules/baton.rules
install -m 600 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/infra.json /home/sl/baton-v11.14aecfb/infra.json
```

## 4. Preflight before launching any process

This calls the lifecycle loader directly. It validates the complete manifest,
dependency order, templates, render ownership, and placeholders but launches
nothing:

```bash
python3 -c 'import sys; sys.path.insert(0, "/home/sl/src/baton/tools"); import infra; manifest = infra.load_manifest("/home/sl/baton-v11.14aecfb"); print("preflight ok: {} contexts, {} services".format(len(manifest["contexts"]), len(manifest["services"])))'
```

Confirm the installed bytes match the reviewed set before start:

```bash
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/infra.json /home/sl/baton-v11.14aecfb/infra.json
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/codex-event-bridge.template.json /home/sl/baton-v11.14aecfb/codex-event-bridge.template.json
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/acp-pc-code.template.json /home/sl/baton-v11.14aecfb/acp-pc-code.template.json
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/baton.rules /home/sl/.codex/rules/baton.rules
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pushcoin-AGENTS.md /home/sl/src/pushcoin/AGENTS.md
```

### The process-domain preflight (W28681) — MANDATORY, in the service context

The ACP launcher owns the agent's PROCESS DOMAIN as well as its mount
boundary, and whether this host permits an unprivileged PID namespace is a
property of THIS launch context. It cannot be established from a nested
sandbox, from a managed agent turn, or by reading the script: a managed
reviewer and a managed implementer both get "No permissions to create new
namespace" and neither result says anything about the service.

Run it as the user and in the context the service starts under, AFTER the
policy files are installed and BEFORE anything is started:

```bash
/home/sl/.config/baton/acp/pc.code/policy/preflight-process-domain.sh
```

It creates the exact domain the launcher composes, starts an escaped
(setsid) descendant and a busy descendant inside it, terminates the domain
owner, and requires both to be gone while an unrelated process of the same
shape is untouched. It removes everything it starts.

**A nonzero result keeps dispatch paused and stops this cutover.** Do not
start the stack, do not resume, and do not install the changed template: a
launcher that contains the agent's writes but not its processes is what let
five tool process groups outlive their turns by 34-36 hours, and that is the
defect W28681 exists to close. Its exit codes name the reason — 2 missing
tooling, 3 no namespace in this context, 4 the probe could not start its own
descendants, 5 the owner ignored SIGTERM, 6 a descendant survived, 7 the
teardown reached an unrelated process.

Byte-compare the two policy files this change installs:

```bash
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/launch-agent-sandboxed.sh /home/sl/.config/baton/acp/pc.code/policy/launch-agent-sandboxed.sh
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/preflight-process-domain.sh /home/sl/.config/baton/acp/pc.code/policy/preflight-process-domain.sh
```

## 5. Start, verify, then resume

```bash
python3 /home/sl/src/baton/tools/infra.py start /home/sl/baton-v11.14aecfb
python3 /home/sl/src/baton/tools/infra.py status /home/sl/baton-v11.14aecfb
/home/sl/opt/baton/v11/14aecfb/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw teams
/home/sl/opt/baton/v11/14aecfb/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw runtime
jq -e '.agent.env.BATON_BIN == .baton.binary and .agent.env.BATON_CONFIG == .baton.config and .agent.env.BATON_PARTICIPANT == .baton.participant and .agent.env.BATON_ROLE == .baton.role' /home/sl/baton-v11.14aecfb/run/context/pc-code-acp.json
```

Require all eight services healthy. The runtime projection must show
`pc.prompt`, `pc.plan`, `pc.tuner`, and `pc.code` live with their exact
identities and Pushcoin working directory; `pc.slaw` remains offline. Check
that only `pc-plan-readiness` and `pc-tuner-readiness` consume Pushcoin Codex
readiness.

Only after those checks pass:

```bash
python3 /home/sl/src/baton/tools/infra.py resume /home/sl/baton-v11.14aecfb --reason "W10198 Pushcoin runner stack healthy"
```

Create one controlled Pushcoin smoke Work at endpoint `pc.rsrch`. The endpoint
sequence is `pc.rsrch` -> `pc.impl` -> `pc.rsrch` -> `pc.ops`; the corresponding
handlers are `pc.plan` -> `pc.code` -> `pc.plan` -> `pc.slaw`. Endpoint names
are not role names: `pc.rview` is not registered and must not appear in the
smoke script. In the fresh `pc.code` turn, require the agent to validate
`BATON_BIN`, `BATON_CONFIG`, `BATON_PARTICIPANT=pc.code`, and
`BATON_ROLE=impl` from its environment before invoking Baton. Confirm each
handler publishes only its `pc.*` identity, no runtime crosses out of
`/home/sl/src/pushcoin`, and no credential failure occurs.

## 6. Rollback

If preflight or startup fails, keep dispatch paused. Stop the partially started
stack if necessary, restore the four `.pre-pc-W10198` inputs (including
Pushcoin's `AGENTS.md` from the mailbox-local backup), start and verify the
original Baton-only stack, and only then resume dispatch. The newly added
ACP template and `pc.code` policy directories may remain inert; the restored
manifest does not reference them.

```bash
python3 /home/sl/src/baton/tools/infra.py stop /home/sl/baton-v11.14aecfb
install -m 600 /home/sl/baton-v11.14aecfb/infra.json.pre-pc-W10198 /home/sl/baton-v11.14aecfb/infra.json
install -m 600 /home/sl/baton-v11.14aecfb/codex-event-bridge.template.json.pre-pc-W10198 /home/sl/baton-v11.14aecfb/codex-event-bridge.template.json
install -m 600 /home/sl/.codex/rules/baton.rules.pre-pc-W10198 /home/sl/.codex/rules/baton.rules
install -m 664 /home/sl/baton-v11.14aecfb/pushcoin-AGENTS.md.pre-pc-W10198 /home/sl/src/pushcoin/AGENTS.md
if test -e /home/sl/baton-v11.14aecfb/launch-agent-sandboxed.sh.pre-domain-W28681; then install -m 700 /home/sl/baton-v11.14aecfb/launch-agent-sandboxed.sh.pre-domain-W28681 /home/sl/.config/baton/acp/pc.code/policy/launch-agent-sandboxed.sh; else rm -f /home/sl/.config/baton/acp/pc.code/policy/launch-agent-sandboxed.sh; fi
rm -f /home/sl/.config/baton/acp/pc.code/policy/preflight-process-domain.sh
python3 /home/sl/src/baton/tools/infra.py start /home/sl/baton-v11.14aecfb
python3 /home/sl/src/baton/tools/infra.py status /home/sl/baton-v11.14aecfb
/home/sl/opt/baton/v11/14aecfb/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw runtime
python3 /home/sl/src/baton/tools/infra.py resume /home/sl/baton-v11.14aecfb --reason "W10198 rollback restored and verified"
```

Skip the first `stop` when no service was launched. Do not resume unless the
restored Baton-only stack is healthy.

W28681: the launcher backup in section 3 is CONDITIONAL because a genuinely
fresh install has no launcher to back up. Both rollbacks are conditional in the
same way and for the same reason: with a backup, restore it; without one,
remove the launcher this cutover installed rather than leaving a changed file
behind under a stack that is being rolled back. `verify.mjs` checks that every
backup a rollback restores is produced on the same path, so the two halves
cannot drift apart again.

## 7. Reconcile an already-installed stack

Use this bounded path for the post-smoke launcher-contract correction. Do not
re-run the pre-cutover source hashes: the reviewed successor is already live.

First verify the corrected staged package, drain, and stop:

```bash
python3 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/verify.py
node /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/verify.mjs
python3 /home/sl/src/baton/tools/infra.py drain /home/sl/baton-v11.14aecfb --reason "install W10198 pc.code authentication and locator gates"
python3 /home/sl/src/baton/tools/infra.py dispatch /home/sl/baton-v11.14aecfb
python3 /home/sl/src/baton/tools/infra.py stop-drained /home/sl/baton-v11.14aecfb
```

Repeat the `dispatch` read until it reports `paused`; `stop-drained` must
refuse without that state. With the stack stopped, back up the two corrected
inputs, provision the isolated credential without exposing it, and install the
reviewed successors:

```bash
install -m 600 /home/sl/baton-v11.14aecfb/acp-pc-code.template.json /home/sl/baton-v11.14aecfb/acp-pc-code.template.json.pre-launch-contract-W10198
install -m 600 /home/sl/src/pushcoin/AGENTS.md /home/sl/baton-v11.14aecfb/pushcoin-AGENTS.md.pre-launch-contract-W10198
install -m 600 /home/sl/.config/baton/acp/pc.code/policy/launch-agent-sandboxed.sh /home/sl/baton-v11.14aecfb/launch-agent-sandboxed.sh.pre-domain-W28681
test -s /home/sl/.claude/.credentials.json
if ! test -s /home/sl/.local/state/acp-baton-bridge/pc.code/claude/.credentials.json; then install -m 600 /home/sl/.claude/.credentials.json /home/sl/.local/state/acp-baton-bridge/pc.code/claude/.credentials.json; fi
test -s /home/sl/.local/state/acp-baton-bridge/pc.code/claude/.credentials.json
test "$(stat -c %a /home/sl/.local/state/acp-baton-bridge/pc.code/claude/.credentials.json)" = 600
install -m 600 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/acp-pc-code.template.json /home/sl/baton-v11.14aecfb/acp-pc-code.template.json
install -m 664 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pushcoin-AGENTS.md /home/sl/src/pushcoin/AGENTS.md
install -m 700 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/launch-agent-sandboxed.sh /home/sl/.config/baton/acp/pc.code/policy/launch-agent-sandboxed.sh
install -m 700 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/preflight-process-domain.sh /home/sl/.config/baton/acp/pc.code/policy/preflight-process-domain.sh
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/acp-pc-code.template.json /home/sl/baton-v11.14aecfb/acp-pc-code.template.json
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pushcoin-AGENTS.md /home/sl/src/pushcoin/AGENTS.md
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/launch-agent-sandboxed.sh /home/sl/.config/baton/acp/pc.code/policy/launch-agent-sandboxed.sh
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pc-code-policy/preflight-process-domain.sh /home/sl/.config/baton/acp/pc.code/policy/preflight-process-domain.sh
```

W28681 makes the changed launcher own the agent's process domain, and the
template now names the preflight as a required policy resource — so BOTH
files above are installed here, and the ACP bridge refuses to start if either
is missing or unreadable.

Then run the MANDATORY process-domain preflight from section 4, in the service
context, before starting anything:

```bash
/home/sl/.config/baton/acp/pc.code/policy/preflight-process-domain.sh
```

A nonzero result keeps dispatch paused and ends this reconciliation: restore
the backups below rather than starting a stack whose launcher does not own its
descendants.

Run the lifecycle preflight from section 4, start the stack, and run every
status, canonical runtime, rendered-context, and fresh smoke gate from section
5. Resume only after the exact launcher variables, the process-domain
preflight, and authentication all succeed.

If reconciliation fails, keep dispatch paused, stop any partial start, restore
the two reconciliation backups, start and verify the previously working stack,
and only then resume:

```bash
python3 /home/sl/src/baton/tools/infra.py stop /home/sl/baton-v11.14aecfb
install -m 600 /home/sl/baton-v11.14aecfb/acp-pc-code.template.json.pre-launch-contract-W10198 /home/sl/baton-v11.14aecfb/acp-pc-code.template.json
install -m 664 /home/sl/baton-v11.14aecfb/pushcoin-AGENTS.md.pre-launch-contract-W10198 /home/sl/src/pushcoin/AGENTS.md
if test -e /home/sl/baton-v11.14aecfb/launch-agent-sandboxed.sh.pre-domain-W28681; then install -m 700 /home/sl/baton-v11.14aecfb/launch-agent-sandboxed.sh.pre-domain-W28681 /home/sl/.config/baton/acp/pc.code/policy/launch-agent-sandboxed.sh; else rm -f /home/sl/.config/baton/acp/pc.code/policy/launch-agent-sandboxed.sh; fi
rm -f /home/sl/.config/baton/acp/pc.code/policy/preflight-process-domain.sh
python3 /home/sl/src/baton/tools/infra.py start /home/sl/baton-v11.14aecfb
python3 /home/sl/src/baton/tools/infra.py status /home/sl/baton-v11.14aecfb
/home/sl/opt/baton/v11/14aecfb/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw runtime
python3 /home/sl/src/baton/tools/infra.py resume /home/sl/baton-v11.14aecfb --reason "W10198 launcher-contract reconciliation rolled back"
```
