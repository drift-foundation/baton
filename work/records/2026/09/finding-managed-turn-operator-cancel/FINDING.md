# Operator cancellation of a managed model turn

## 2026-09-17 — confirmed owner request

During W194457, owner direction changed while Claude held a long-running turn.
Thread messages and a poke did not establish that the active model reread the
new spec. The ACP bridge documents serialized wakes and no steering of busy
sessions. Its process signal handlers implement shutdown via SIGINT/SIGTERM,
not a supported SIGUSR1 turn-interruption command. Owner explicitly requested
the ability to cancel and assigned this separate Work to tuner.

ACP defines `session/cancel` for cancelling the current prompt, with a cancelled
prompt result; see https://agentclientprotocol.com/protocol/v1/prompt-turn.
The missing capability is an operator-facing bridge control, not a need for a
new Unix signal convention. Local starting points: tools/acp-baton-bridge/src/
acp_agent_session.mjs and acp_baton_bridge.mjs, plus the bridge README.

## Accepted outcome

Provide a documented operator command to target and cancel the current managed
ACP turn without restarting the whole stack. Route through the existing session
owner and protocol connection; do not create a second readiness consumer or a
second agent session under the same participant. Report requested versus settled
cancellation honestly. Reject stale requests targeting a replaced turn/session;
do not accidentally cancel the next turn. Handle repeated requests and idle
targets explicitly.

Preserve files, session history and canonical Work ownership. Cancellation is
not Work completion, claim release, rollback, or proof that every external effect
has stopped. Preserve the existing descendant-process settlement guarantees;
failure or timeout must leave an actionable status rather than falsely claiming
safe continuation. Do not automatically redispatch the old instruction after
cancellation. Provide an explicit continuation path carrying the updated spec
locator/instruction; require the resumed agent to acknowledge what changed.
A cancellation acknowledgement alone is not proof of rereading.

First delivery targets the current Claude ACP lane. Keep protocol-specific
cancellation behind the adapter; do not require a broader Codex/v12 scheduler
redesign or new TUI. Reuse existing control/deployment facilities where suitable.
Document exact commands and behavior, including cancellation during a tool call
and claim-held continuation. Any missing independent prerequisite is separate
Work, not an excuse to grow this into a general orchestration redesign.

No interruption of W194457, actual production cancellation, live provider trial,
stack restart or Git mutation is authorized by this implementation assignment.
Use deterministic fake ACP peers/process fixtures; independent review follows.

## Coordination

This Work is separate from W194457 and must not take its v12 product/test paths.
Owner selected baton.tuner for implementation. Prompt records coordination only.

## 2026-09-17 — implementation contract, tuner claim 195317

Revalidated the current bridge: one ACP process domain per delivered turn,
followed by canonical claim settlement. The pinned SDK exposes `cancel` as a
notification; its send completion is not cancellation completion. The official
prompt-turn specification requires the original prompt response to carry
`stopReason=cancelled`; updates can still arrive before that response.

Implement local operator control through the same bridge executable and a
private Unix socket in the configured state directory. Status exposes an opaque
bridge incarnation, session and turn ID. Cancel compares all three, persists an
operator hold before notification, and reports requested separately from prompt
response, process-domain exit and canonical claim settlement. A bounded cancel
wait uses the existing setup timeout, then the existing domain teardown. A
timeout or protocol failure remains visible even after teardown proves exit.
No production process is touched by this implementation.

The hold survives restart and suppresses all automatic readiness delivery.
Explicit continuation names the held target, a unique request ID, revised spec
locator, and changed instructions. It revalidates the exact canonical action
and retains the selected ACP session. It requires the agent to read the revised
spec and emit an acknowledgement identifying the request and changes. Record
observed acknowledgement separately; text alone cannot prove comprehension or
external-effect safety. Missing acknowledgement/failure retains the hold. A
restart during unsettled cancellation or continuation refuses continuation until
operator investigation; it never assumes a prior domain exited.

File ownership announced in T195314 message195328: only the ACP bridge source,
new operator control, fake peer/focused tests, package test entry, README and this
dossier. Shared bridge infrastructure and W194457 paths remain with their owners.

Operational finding: `PROGRESS.md` was absent (ENOENT) on the initial dossier
read. There is no earlier author progress to recover; initialize that required
record under this claim. The accepted FINDING and PLAN were readable in full.


## 2026-09-17 — deployed shutdown evidence limitation

Owner sent SIGTERM to Claude bridge PID3637911. Log reports agent process
domain teardown, then aborted claim reconciliation, incident and runtime-end
publication; W194457 claim episode195081 remains. Read-only inspection of
/home/sl/.config/baton/acp/baton.claude/policy/launch-agent-sandboxed.sh finds
mount-only bwrap, without the documented --unshare-pid/--die-with-parent
contract. Therefore the teardown log cannot establish descendant absence for
this deployment. Do not restart/release on that log alone. Docker listing at
inspection showed only unrelated mdb114-a. Test output /tmp/w194457-full-195090.txt
reports 7941 tests in 651.803s, 111 failures, 28 errors, 21 skipped and a warning
that subprocess298342 was still running when the output was written. That PID
may be namespace-local and is not authority to kill a same-numbered host PID.
No Git restoration, claim release or runner restart performed by prompt.
This is deployment evidence for recovery, not an expansion of cancellation
implementation into unrelated test corrections.

## 2026-09-17 — reviewer triage after operational handback, claim 195442

**Observed:** tuner handback event195430 reports that a resumed standalone claim
was refused while dispatch was draining. This reviewer successfully claimed
W195314 through the supplied canonical launcher at seq195442. The earlier
admission refusal is therefore not a current blocker to this assignment; this
does not prove that the draining/resumed-claim interaction has been corrected.
No dispatch setting, production process or Work recovery state was changed.

**Confirmed:** partial product files and both new operator-control files remain
present. README still lacks the new control command documentation. Author progress
does not contain a completed verification result or candidate handoff. This is an
implementation return, not a candidate acceptance review.

**Observed:** `src/operator_control.mjs` currently instructs a continuing agent
holding the claim to continue without another claim. Repository AGENTS.md requires
a successful standalone claim on every readiness turn. Before delivery, reconcile
this generated instruction with current policy; do not silently override policy
inside a continuation prompt. If the draining/resumed-claim boundary still needs
a policy or protocol change, record and route that prerequisite separately rather
than assuming this successful fresh claim proves resumed admission.

Return to the explicitly assigned tuner to finish the existing scope, document
operator commands, run focused deterministic verification and submit a complete
candidate for independent review. Reviewer verification spending this triage: 0s
(no tests executed); prior author cumulative spending remains unknown.

## 2026-09-17 — tuner continuation clarification, claim 195453

The prior generated instruction to skip a held claim is superseded: continuation
requires canonical detail and the standalone claim required by repository policy.
A refusal stops execution and is reported through the authorized handback; the
bridge never bypasses dispatch draining or grants execution authority. This
corrects the partial prompt, not repository policy or protocol semantics.
Continuation also checks the loaded ACP session against the held session before
sending any revised prompt, including after restart. A mismatched selection
retains the hold without spending a turn. Existing process-domain deployment
requirements remain mandatory; direct fake-peer exit evidence is not proof of
production descendant containment.

## 2026-09-17 — independent review, claim195483

**Confirmed:** candidate195453 passes 138 deterministic tests independently and
matches its seven-file manifest. The prior generated claim-policy conflict is
corrected. **Observed defect:** admitting a continuation replaces the held turn
target before retry matching, so repeating the exact accepted request fails
`stale held target` during execution and after completion. This contradicts the
documented continuation idempotency guarantee. Preserve accepted request identity
separately from the current turn identity; identical retries must not dispatch a
second turn and conflicting retries must still refuse. Exact evidence and bounded
test correction are in review-2026-09-17T15-12-08Z.md. Candidate is not accepted.

## 2026-09-17 — retry correction, tuner claim195504

Confirmed review reproduction against current handle/prompt ordering. Persist the
accepted continuation target inside the continuation payload and compare that
immutable request before comparing the current held turn. Admission and completion
may update the current target without changing the retry identity. Exact retries
return current status only; changed target or instructions refuse. Cancellation
still compares the active/current target, never the continuation retry target.
Focused regression ownership remains test/operator_control.test.mjs.

## 2026-09-17 — independent acceptance, claim195517

Candidate195504 resolves the prior continuation retry finding: accepted request
identity survives admission, completion and restart, while conflicting retries
and stale cancellation still refuse. All seven product/current snapshot hashes
match the replacement manifest. Independent verification passed139/139 in
14.642842104s. The earlier non-acceptance is superseded for candidate195504 only;
historical reviews and candidate195453 remain unchanged. Exact accepted digest,
path set, test expectation assessment and production-evidence limits are pinned
in review-2026-09-17T15-16-29Z.md. Source candidate accepted; owner approval and
any later deployment remain separate. Pass the prepared change to baton.ops.
