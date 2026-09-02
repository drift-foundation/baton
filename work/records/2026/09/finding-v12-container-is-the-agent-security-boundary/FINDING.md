# Make the container the v12 agent permission boundary

Work: W64268

## Observed

Live isolated W61984 attempts launched the real Claude worker with
`--permission-mode acceptEdits`. Claude could edit its private candidate tree,
but ordinary verification commands such as the task's exact Python test were
repeatedly refused as requiring approval. The outer worker later ran the same
command, proving that the command itself belonged inside the container and was
not a host-authority request.

The existing decision is recorded in
`work/records/2026/08/finding-v12-first-useful-dogfood-task/findings/finding-real-claude-adapter-image/FINDING.md`.
It selected `acceptEdits` as a deliberate departure from the read-only
ping-pong spike. Live dogfood has now shown that this is still an inner command
allowlist, not merely permission to edit.

## Decision — 2026-09-01

The v12 worker container is the agent's security and disposal boundary.
Inside an accepted trusted-worker runtime, the agent may execute arbitrary
tools available in the image without per-command approval, including shells,
tests, compilers and repository-local helpers. The Claude adapter therefore
uses the CLI's non-interactive permission-bypass mode rather than
`acceptEdits`; the exact current spelling to implement and golden-test is
`--dangerously-skip-permissions`.

This decision removes only the redundant policy inside the container. It does
not grant host authority. The runtime still has:

- read-only staged input and attempt credential mounts;
- private writable scratch and declared output only;
- no host Docker socket, host process namespace, host devices or privileged
  container posture;
- manager-owned start, stop, collection, retention and disposal;
- the configured network and resource posture, which are runtime grants rather
  than interactive command approvals.

The worker need not run as host root and receives no capability to mutate the
canonical repository or Baton authority. Root-like freedom inside an
unprivileged disposable container is not host root.

## Acceptance

- The Claude provider argv no longer contains `--permission-mode
  acceptEdits`; it explicitly enables permission bypass in the isolated
  worker.
- Golden argv and live dogfood prove that an ordinary Python verification
  command runs without an approval request.
- The OCI launch posture still proves the external boundaries listed above.
- No v11 runner or host execution policy is widened.
- Implementation is produced through an isolated v12 attempt and independently
  reviewed before import.

## Reviewer revalidation — 2026-09-01

### Observed

The current tree still composes the provider in one closed tuple at
`v12/worker/claude_agent.py:149`:

```text
claude --print --permission-mode acceptEdits --output-format json PROMPT
```

`TheProviderArgvAndEnvironmentAreClosed.
test_the_argv_is_exactly_the_pinned_vector_plus_one_prompt` is the one golden
owner at `v12/python/tests/manager/test_claude_agent.py:233`. No other product
source contains `acceptEdits`, `--permission-mode`, or a permission-bypass
spelling. The smallest production patch is therefore the provider tuple, not
the worker entry, manager, image recipe or OCI adapter.

The locally installed Claude Code 2.1.250 advertises three distinct surfaces:

- `--dangerously-skip-permissions` activates bypass immediately;
- `--allow-dangerously-skip-permissions` merely permits bypass to be selected
  later and does not activate it; and
- `--permission-mode bypassPermissions` is a mode-valued alternative.

The approved decision intentionally names the first. Do not substitute the
`--allow-...` flag or retain `--permission-mode` with a new value: both would
make the implementation differ from the ruled and live-golden command.

The worker image remains pinned to Claude Code 2.1.247 in
`v12/worker/Dockerfile.claude:41-42`, with the same version asserted by
`tests/manager/test_dogfood_image.py`. This managed reviewer could not query
that exact built image because Docker's daemon socket is not reachable under
the installed reviewer authority. Exact 2.1.247 argv acceptance is therefore
an explicit isolated-image gate below, not a fact inferred from the host
2.1.250 binary.

The external isolation boundary is independent of the provider tuple and is
still explicit in `worker_manager.oci`:

- `RESTRICTIONS` drops every capability, sets no-new-privileges, fixes uid/gid
  65532, makes the image root read-only, applies one explicit network, and
  bounds pids, memory, CPU and private no-exec tmpfs mounts;
- execution posture admits only manager-proved `inputs` and `workspace`
  roots; inputs are read-only and only workspace may be writable;
- credential and launch-document mounts are always read-only at fixed targets;
  and
- the closed run vector has no privileged flag, Docker socket, host PID/device
  grant or caller-supplied arbitrary mount.

Focused current-tree baselines pass 86 Claude-adapter tests and 111 OCI-vector
tests. `tests.manager.test_input_delivery` ran 30 non-Docker cases, but its two
required real-daemon classes refused at setup because `/var/run/docker.sock`
is inaccessible. No escalation was requested; the exact daemon/image proof
belongs to the isolated v12 attempt.

### Confirmed patch boundary

Change only:

1. `v12/worker/claude_agent.py`: replace the three-word
   `--permission-mode acceptEdits` fragment with the one activation flag
   `--dangerously-skip-permissions`; preserve `--print`, structured JSON output
   and the prompt as the final word.
2. `v12/python/tests/manager/test_claude_agent.py`: update the exact golden
   vector and add negative assertions that `--permission-mode`, `acceptEdits`
   and `--allow-dangerously-skip-permissions` are absent while the activation
   flag occurs exactly once.

No OCI or host-runner production change is authorized. A candidate touching
`worker_manager/oci.py`, the v11 runner, host policy, mount topology, network
grant, user, capabilities or lifecycle expands beyond this decision and must
return for plan revision.

### Required isolated verification

The fresh v12 attempt must preserve two distinct proofs:

1. Inside the rebuilt 2.1.247 image, `claude --help` names
   `--dangerously-skip-permissions`, and the focused golden adapter suite sees
   the exact closed argv.
2. One live provider task edits only its private candidate and invokes an
   ordinary Python verification command itself. The provider completes without
   an approval request; the outer worker independently reruns the same frozen
   command and compares the candidate result.

The regression matrix also keeps structured-output parsing, bearer exclusion,
prompt bounds, timeout/drain behavior and source-tree containment unchanged.
The OCI vector and input-delivery gates must show that bypassing the inner CLI
policy did not change the container's user, capabilities, mounts, network,
namespaces, devices or manager-owned lifecycle.

### Scheduling interaction

W61984's run8 proposal is currently changes-requested and needs its own bounded
repair. This Work remains ordered after W61984: the permission correction is
what lets the next isolated worker execute its own verification, but it must
not be folded into or used to rewrite the finalization candidate already under
review. The scheduler dependency should remain explicit until W61984 closes.

### Scheduling update — 2026-09-02

W61984 closed satisfying after its independently reviewed proposal was
integrated. The dependency described above is satisfied. W64268 is ready for a
separate isolated v12 attempt; it remains forbidden to fold this correction
into W61984 or implement it through the v11 host runner.
