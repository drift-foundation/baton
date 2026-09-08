# Complete bounded live package — W106673

Prepared by baton.tuner under claim 107665, 2026-09-07. This is a candidate for
baton.bug independent review and then baton.ops separate live-execution approval.
Preparation ran no Docker container, namespace operation, provider request or
real credential delivery. The accepted deterministic and offline transport
evidence remains unchanged. FINDING.md, PLAN.md and REAL-SESSION-CHECKPOINT.md
own the decision and acceptance history.

## Exact operations

Offline verification, with no source credential or Docker access:

```sh
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller.py --audit
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/test_live_package.py
```

Proposed ONE owner-operated invocation, only after independent review and the
separate live-execution approval:

```sh
sudo -- /usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller.py --run
```

No runtime choice operands, build, pull, installation, production configuration,
service, arbitrary target, recovery mode or automatic retry. No managed agent
executes this command. The manifest binds every package artifact and all 70
current baton_v12 Python source files plus the existing user credential reader.
Any initial file/hash drift refuses. Before credential use the controller copies
and rechecks the runtime source into a private fixture snapshot; imports use that
snapshot, preventing concurrent K custody edits from changing lazy imports.
This is source preservation, not production adoption or a second manager service.

## Runtime and authority

Image: `sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f`.
The container must report Claude Code `2.1.247`; the host CLI is never used.
Configured model argument is exactly `claude-fable-5[1m]`. This candidate requires
the stream's actual model field to be exactly `claude-fable-5`; this expectation
is unverified live and a mismatch makes the run inconclusive, with no alias or
fallback substitution. Both arms must observe the same identity.

Exactly three possible containers: retained-first, restored-first, restored-second.
Each has user/group 65532:65532, supplementary group 65532, cap-drop ALL,
no-new-privileges, read-only root, default Docker seccomp, no host PID namespace,
no published ports, 64 PIDs, 2 GiB memory and one CPU. `/tmp` is a 64 MiB
nosuid/nodev/noexec tmpfs. Writable binds are one private workspace at `/output`
and one private fixture session directory at `/session`. Read-only binds are the
reviewed supervisor and the single existing credential delivery slot. No socket,
whole home, alternate workspace alias or host namespace is mounted.

The controller resolves the built-in local default `bridge` network once, checks
its name/driver/default-bridge marker/non-internal state and pins its full ID
before any container create. All three containers use that ID. This is ordinary
Docker outbound access, **not provider-only egress enforcement**. The network ID
could not be inspected during preparation because Docker socket access was
denied; no stronger command or escalation was attempted.

Existing credential delivery is already resolved by owner M107362. The source
remains `/home/sl/.claude/.credentials.json`, read only by the existing
`UserCredentialSources` under effective UID 1000, matching its private-source
ownership checks. The root controller restores its effective UID in `finally`.
A generated private nonsecret locator registry is owned by UID 1000. Existing
`CredentialHome.materialize` creates each attempt-private volatile slot under
a fresh manager-only `/dev/shm` directory; the source itself is never chmodded,
chowned, manually copied, hashed, logged or mounted into the worker.

A disposable fixture ControlStore and existing workspace-group APIs hold group
65532. Only the operator process's supplementary groups temporarily include that
group, restored at ending; no host group configuration is changed. The runtime
source snapshot and fixture store are private experiment resources, disjoint
from the authoritative v11 ledger and production manager stores.

The worker home symlinks its credential entry to the read-only logical slot
`/run/baton/credentials/claude`, as the existing delivery boundary specifies.
Session state stays outside `/output` and is reused only by the restore arm.
The old container is confirmed stopped before normal credential teardown and
before replacement materialization. Uncertain cleanup retains the delivery and
reports failure; it never reports the slot released.

## CLI and bounded transport

All three CLI processes use exactly:

```text
/usr/local/bin/claude --print --input-format stream-json --output-format stream-json --verbose --tools Bash,Read,Write,Edit --setting-sources= --strict-mcp-config --mcp-config {"mcpServers":{}} --dangerously-skip-permissions --model claude-fable-5[1m] --max-turns 8 --max-budget-usd 1 SESSION_MODE UUID
```

`SESSION_MODE UUID` means `--session-id <fresh UUID>` for each first container,
and `--resume <restored-first actual UUID>` for restored-second. UUIDs are
generated by the fixture, then must match actual init/result observations. No
`--continue`, session fork or unrelated fresh-conversation substitute is allowed.

The accepted request-ID-bound streaming initialize handshake precedes user work.
Stdin remains open; the same retained subprocess receives both turns. CLI cwd,
home, cache and session state are all outside `/output`. Each idle process tree
must contain exactly the pinned supervisor and Claude child, with unchanged
host PID/start time/executable/mount namespace and live pidfds. An extra idle
helper/tool process is a refusal, not a reason to broaden the check automatically.

There are at most four user turns, two retained and one per restored container;
180 seconds per user turn and a 900-second overall runtime deadline. The first
720 seconds permit work; the last 180 are reserved for ending. Root and worker
alarms enforce the work cutoff, and cleanup has the overall deadline plus
30-second per-operation bounds. Deadline exhaustion reports unconfirmed cleanup
and preserves the delivery. No further Docker operation is admitted after that
deadline. Result/export flushing follows ending; host SIGKILL recovery and
hard real-time guarantees for uninterruptible kernel operations are not claimed.

`--max-turns` was absent from the accepted help inventory. The six live options
(resume, session-id, max-turns, max-budget-usd, model, bypass permissions) and
their combined live behavior have not been proved. Unknown/rejected options
fail the run; there is no fallback argv. Proposed USD1 per CLI invocation means
a nominal USD3 for the three processes; **a hard billing/quota cap is unverified**.
Post-result checks require success, `is_error=false`, at most eight reported
turns, and finite reported cost between zero and USD1. That observed-cost check
cannot prevent an already incurred charge or establish subscription billing.

Provider stdout uses deadline-bound reads, a 256 KiB line bound and 4 MiB per
turn. Only actual session/model identity, completion time, turn count and reported
cost survive projection. Assistant text, tool arguments, raw errors, stderr and
transcripts are never exported. Unexpected interactive control requests refuse.

## Custody, comparison and ending

The accepted deterministic Gate, ordinary-unmount helper and mount topology
checks are reused unchanged. Before detach, process identity and quiescence are
checked, the durable gate becomes uncertain, and ordinary `umount2(flags=0)` is
the decisive operation. Both actual mount absence and denied worker access are
required for a revocation receipt. EBUSY, missing acknowledgment, identity drift,
timeout or any ambiguity stops the comparison and requires confirmed shutdown;
no lazy/forced detach or worker mount authority exists.

The only artifact reader runs after exact receipt consumption. It holds a
no-follow workspace descriptor and accepts only tiny regular, single-link files
with the exact expected path set and bytes; it executes no agent-authored code.
Wrong correction/token results are inconclusive. The same initial prompt and
nonce, empty initial workspace, correction prompt and five-second review delay
apply to both arms. The correction omits the remembered nonce. Retained success
requires the same live actual Claude process/session; restored success requires
a new process, the old actual session ID and remembered-token correction.

The main metric is first-turn completion to the first safely verified useful
correction. Results also separate review readiness, correction response, final
revocation/verification, ordinary detach/reattach, old stop, and replacement
startup/initialize. Actual resume readiness beyond initialization is observed
through the correction result; it is not inferred from an idle handshake.
Fixed run order, independent session histories/provider sampling, container
startup, billing behavior and internal cache/context costs cannot be held equal
or attributed by this one pair. No performance outcome is claimed in preparation.

Confirmed ending checks exact container/image/run labels, Docker stopped/PID0,
the pinned init pidfd and absence of any host-visible process in its mount
namespace. A failed Claude child does not prevent that container shutdown.
Credential removal uses existing normal teardown only after confirmed ending.
A lost create response preserves the exact run label and delivery for operator
repair, with no guessed container ID, broader kill or automatic retry.

The first printed path is the root-owned private retained experiment directory.
The second is a UID1000-owned private export directory under
`/tmp/baton-w106673-live-export-*`. Only package/network/arms/result JSON and
three possible per-arm event/gate pairs are exported, with exact original-byte
SHA256s in PROVENANCE.json. The exporter never walks session/workspace trees or
copies the source registry, delivery, runtime snapshot, database or transcripts.
Stopped containers, private session state and ordinary fixture files remain for
inspection. Normal credential teardown is the only automatic sensitive removal.

Independent review should bind the manifest digest and exact invocation, inspect
the actual gates and safe projections, then route to baton.ops. Later live
evidence still needs independent exported-hash/container/process/session/custody
review. This candidate supplies no production adoption authority.
