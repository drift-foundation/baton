# Real-Claude preparation checkpoint — W106673

Prepared by baton.tuner under claim 107264. This package supplies an exact
offline transport preflight and independently testable task/measurement contract.
It is **not yet the credential-bearing detach/restore runner**. Its two remaining
preparation gates are exact-image transport evidence and the credential-delivery
clarification in M107310. Return the prepared bytes to independent review before
the operator checkpoint; no managed runtime execution was performed.

## Selected inputs and their provenance

| Input | Current disposition |
| --- | --- |
| Image | Proposed reuse of installed sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f. Selected in the W85497 image dossier; exact local inspection succeeded. No build/pull. |
| CLI | Retained W85497 exact-image gate records 2.1.247. Host resolves to 2.1.250 and was not substituted. Offline probe requires exact 2.1.247. |
| Model argument | Current non-secret /home/sl/.claude/settings.json member model is exactly claude-fable-5[1m]. Preserve this spelling for both arms; record the actual resolved model separately from the context-window suffix at live initialization. No model/version fallback. |
| Credential source | Owner M107302 nominates /home/sl/.claude/.credentials.json. Only metadata was inspected: regular file, 0600, uid1000:gid1000, no extended ACL. Bearer bytes were not opened, copied, read, hashed or logged. |
| Credential destination | /run/baton/credentials/claude, linked from fixture-private provider HOME. Source readability is unresolved under the no-copy restriction; see below. |
| Network | Owner accepts ordinary Docker outbound access without published ports. Propose the existing default bridge for the live pair; exact network-ID inspection was denied by the managed Docker boundary and remains required before freezing that package. This is not a provider-only egress firewall. Offline preflight is network=none. |
| Limits | Owner approves one pair, four user turns, 180 seconds per user turn and 15 minutes overall. Proposed CLI max-turns=8 and max-budget-usd=1 per process remain review inputs. There are three process invocations. USD3 is not an established hard billing or subscription-quota cap. |

Input observations are in evidence/real-session-inputs.json. The older
deterministic proof and scripts remain byte-for-byte intact.

## Exact next operator action, after independent review and owner approval

    /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/real_session_preflight.py --operator

This requires access to the local Unix Docker daemon, not host namespace/mount
privilege. If that authority is absent, return the result; managed agents do not
escalate. The script creates exactly one labelled disposable container, with:

- The fixed image above, --pull=never, overridden entrypoint /usr/bin/python3.
- User65532:65532, cap-drop ALL, no-new-privileges, read-only root, network none.
- One read-only bind containing only the exact staged probe.py, no source,
  workspace, credential, user home or Docker socket.
- 64MiB noexec tmpfs at /tmp, 1GiB memory, one CPU, 64 process limit.
- Closed child environment and cwd /tmp. No provider environment inheritance.
- Claude --version, --help and one streaming initialize control request.
  No user message, model request, restore request or provider authentication.

The script checks the required flags and correlated initialize success, retains
stdin, observes the same CLI PID/start/pidfd alive for one second, then ends it.
It reports only fixed outcome values, flag booleans, help digest and numeric
identity/timing. Provider stderr is discarded and raw structured responses are
never exported. The version/flag/initialization checks have bounded reads and
deadlines. Flag presence alone does not prove those flags' live semantics.

The printed /tmp/baton-w106673-session-preflight-* root contains staged script,
registration.json and result.json. Registration records full container identity
before starting it. Failed identity checks refuse cleanup; otherwise the exact
labelled container is stopped and its stopped state recorded. Nothing removes
containers, files or images. A failed create may leave an unregistered container;
the run nonce and label identify it for operator inspection. A passing result
requires stopped state and exit0.

This action does not repeat the accepted privileged OS experiment. Even a pass
proves only initialized idle transport: two real turns, actual session identity,
session restoration, budget semantics and handle release remain unproved.

## Why credential delivery is an unresolved boundary

The current per-user registry in v12/python/DEPLOYMENT.md, W52821, selects a
private source by provider/reference. tools/dogfood_operator.py reads that source
as the invoking user. worker_manager/credentials.py:materialize creates a
separate volatile file, sets its group/mode before writing the bearer, and
provides the worker a read-only bind of that delivered slot. It does not alter
the private source's mode or translate its owner.

M107302 says both “existing per-user credential mechanism” and “no copying”.
The existing mechanism necessarily materializes separate bytes. A direct bind
of this 0600 uid1000 source is not a verified delivery for uid65532, and the
accepted deterministic runner excludes user-namespace remapping. No installed
no-copy alternative was found in the reviewed source/docs. Historical spike
staging also copied a bearer and is explicitly not a current instruction.

M107310 therefore requests a precise ruling: either authorize the existing
manager-owned volatile delivery as the intended exception, or identify the
already-installed mechanism intended by the owner. This package adds no source
reader, credential staging, chmod/chown, mapping or runtime-uid workaround.
Any changed delivery selection must be pinned before preparing its implementation.
The nominal logical slot is not a credential source and does not make it readable.

## Proposed full runner after those gates

Preserve the accepted Gate and ordinary umount2(flags=0) mechanism in the reviewed
deterministic host_runner.py. Prepare a separate real-session controller; do not
overwrite the accepted deterministic artifacts. No production manager is imported.

The container init is a small supervisor. Claude starts once with cwd /session/work,
and HOME, cache, IPC and persisted conversation state under /session, outside
/output. Session storage is private fixture state, separately mounted from both
workspace and credentials and retained across the restart arm. Do not copy a
whole home or export raw conversation logs to repository evidence. The credential
link targets the separate read-only slot; it is never part of an export.

Proposed transport is --print --input-format stream-json --output-format
stream-json --verbose, with explicit --setting-sources=, strict empty MCP config,
a bounded explicit tool set, the exact model and limits. Send two user frames
over the same still-open stdin for retention. Restart uses a new container/process
and --resume=<actual-first-session-UUID> against that arm's original session state;
it must never use --continue, a fresh conversation or --fork-session. Actual argv
is not frozen until the pinned-version probe and delivery ruling are accepted.

Replace the deterministic single-PID check with an explicit runtime process-tree
proof, not its deletion. Pin the container/init and real CLI host PIDs, start
times and pidfds, namespace, workspace device/inode and actual CLI session UUID.
At each handoff enumerate all container processes and verify membership in the
pinned init tree, same mount namespace, no unexpected retained tool descendants,
outside-workspace cwd and unprivileged posture. Revalidate before mount mutation.
Unexpected descendants, identity drift or inaccessible evidence keep gates closed.
A model “done” event is only a request to attempt the handoff.

Ordinary unmount in that actual namespace is decisive. EBUSY, interrupted receipt,
missing acknowledgment or unexpected state requires confirmed shutdown before
consumption or new assignment. Controller loss discards authority on reload.
Topology must exclude every alternate workspace alias. During detached review
the same Claude process remains alive but receives no new user frame.

The restart arm stops the original container, confirms init/CLI exit and absence
of namespace survivors, consumes/verifies the first result, then starts a new
container against the same workspace and that arm's session storage. The retained
arm consumes/verifies after detach, waits the same five-second review interval,
reattaches, and submits the identical correction. Both arms end correction with
ordinary detach or mandatory shutdown before the verifier reads any output.

## Task, equivalence and timing

evidence/real_session_contract.py supplies the two exact prompts and verifier.
Both initially empty workspaces receive the same first prompt and same generated
32-hex token for this pair. First turn writes the exact scale-by-two function.
The correction writes scale-by-three plus the remembered token from the original
conversation. The correction prompt never repeats the token. A fixed-byte
verifier checks the full allowed file set without executing agent-authored code.
The future collector must use bounded no-follow reads of regular, single-link
files only after the valid consumption receipt. No verification read occurs while
the writer still has access.

Run retained first, restored second, once each, with no retries. Both first turns
are real model turns: there are four user messages total. Preserve identical
image/model/instructions/initial bytes/review delay. Provider sampling, separate
initial conversations and serial run order cannot be held identical; report
them as limitations. Remembered-token success supplements observed actual session
identity and resume transport; it does not replace process or custody proof.

Record monotonic end-of-first-work, review-ready, correction dispatch, correction
completion and first safely verified useful correction. Also record container/
CLI start and observed initialize events; do not label initialize acknowledgment
as full restored-context readiness. The main interval is end-of-work through the
verified correction and includes the actual custody/verification work. Report
detach/attach/shutdown/container-start intervals and the fixed review delay
separately. The comparison contract rejects changed retained processes, absent
resume identity, unequal inputs, unsafe-consumption claims and invalid time order.
Its booleans must come from the controller's actual observations, not agent text.

## Budget limitation and references

The CLI reference describes --max-budget-usd as an API-cost stopping control.
The cost guide says subscription session-cost figures are not billing. Presence
of that flag and a nominal three-process sum do not establish exact enforcement,
overshoot behavior, resume accounting or a hard account-level cap for the nominated
authentication. No credential or auth-status command was used to infer account
details. Report USD3 as unverified, keep the approved time/user-turn limits, and
obtain owner disposition before live execution rather than changing auth/billing.

Read on 2026-09-07; current online documentation/source is decision support,
not a substitute for exact-image verification:

- [CLI reference](https://code.claude.com/docs/en/cli-usage): flags for streaming,
  named session creation/restoration, tools and limits.
- [Streaming input](https://code.claude.com/docs/en/agent-sdk/streaming-vs-single-mode):
  a long-lived process can receive sequential user inputs.
- [Anthropic SDK subprocess transport](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/_internal/transport/subprocess_cli.py):
  stream-json transport and explicit resume/session arguments.
- [Anthropic SDK client](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/client.py):
  initialize followed by correlated user frames on the existing transport.
- [Anthropic SDK control protocol](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/_internal/query.py):\n  the initialize request supplies subtype and optional hooks, then correlates its response.\n- [Cost guide](https://code.claude.com/docs/en/costs): subscription usage and
  session estimates have different billing meaning.

Validation: four preflight parser/identity tests and four verifier/comparison
tests pass. No offline container or real Claude turn was executed. Exact script
and document hashes are in evidence/real-session-preparation-manifest.json.
