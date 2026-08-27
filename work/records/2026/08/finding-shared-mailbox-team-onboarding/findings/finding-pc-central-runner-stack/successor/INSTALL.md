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
python3 /home/sl/src/baton/tools/infra.py start /home/sl/baton-v11.14aecfb
python3 /home/sl/src/baton/tools/infra.py status /home/sl/baton-v11.14aecfb
/home/sl/opt/baton/v11/14aecfb/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw runtime
python3 /home/sl/src/baton/tools/infra.py resume /home/sl/baton-v11.14aecfb --reason "W10198 rollback restored and verified"
```

Skip the first `stop` when no service was launched. Do not resume unless the
restored Baton-only stack is healthy.

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
test -s /home/sl/.claude/.credentials.json
if ! test -s /home/sl/.local/state/acp-baton-bridge/pc.code/claude/.credentials.json; then install -m 600 /home/sl/.claude/.credentials.json /home/sl/.local/state/acp-baton-bridge/pc.code/claude/.credentials.json; fi
test -s /home/sl/.local/state/acp-baton-bridge/pc.code/claude/.credentials.json
test "$(stat -c %a /home/sl/.local/state/acp-baton-bridge/pc.code/claude/.credentials.json)" = 600
install -m 600 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/acp-pc-code.template.json /home/sl/baton-v11.14aecfb/acp-pc-code.template.json
install -m 664 /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pushcoin-AGENTS.md /home/sl/src/pushcoin/AGENTS.md
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/acp-pc-code.template.json /home/sl/baton-v11.14aecfb/acp-pc-code.template.json
cmp /home/sl/src/baton/work/records/2026/08/finding-shared-mailbox-team-onboarding/findings/finding-pc-central-runner-stack/successor/pushcoin-AGENTS.md /home/sl/src/pushcoin/AGENTS.md
```

Run the lifecycle preflight from section 4, start the stack, and run every
status, canonical runtime, rendered-context, and fresh smoke gate from section
5. Resume only after the exact launcher variables and authentication succeed.

If reconciliation fails, keep dispatch paused, stop any partial start, restore
the two reconciliation backups, start and verify the previously working stack,
and only then resume:

```bash
python3 /home/sl/src/baton/tools/infra.py stop /home/sl/baton-v11.14aecfb
install -m 600 /home/sl/baton-v11.14aecfb/acp-pc-code.template.json.pre-launch-contract-W10198 /home/sl/baton-v11.14aecfb/acp-pc-code.template.json
install -m 664 /home/sl/baton-v11.14aecfb/pushcoin-AGENTS.md.pre-launch-contract-W10198 /home/sl/src/pushcoin/AGENTS.md
python3 /home/sl/src/baton/tools/infra.py start /home/sl/baton-v11.14aecfb
python3 /home/sl/src/baton/tools/infra.py status /home/sl/baton-v11.14aecfb
/home/sl/opt/baton/v11/14aecfb/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw runtime
python3 /home/sl/src/baton/tools/infra.py resume /home/sl/baton-v11.14aecfb --reason "W10198 launcher-contract reconciliation rolled back"
```
