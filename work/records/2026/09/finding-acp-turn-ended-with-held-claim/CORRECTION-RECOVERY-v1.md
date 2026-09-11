# Selected correction and bounded recovery proposal

Accepted by Slawomir at return133489, 2026-09-10T04:23:06Z: exact policy/config
scope and separate120s allocation approved; recovery authorized only after
independent review and all preconditions. This acceptance supersedes this
document's historical pending-approval wording below. Current assignments are
in PLAN.md and the concrete operator sequence is OPERATIONS-CHECKLIST-v1.md.

Prepared by baton.codex under W133361 claim133448 for owner return133444.
Decision owner: FINDING.md, 2026-09-10T04:16:25Z entry. This is a reviewable plan,
not a record of completed changes or authority to recover the product claim now.

## Intended behavior

Every managed implementer Work turn reads the current canonical handoff and
discussion before editing. It continues authorized work within the live turn,
or explicitly hands incomplete work back with evidence and cumulative spending.
A final response occurs only after canonical confirmation that the claim is
released. Durable progress is still required and never substitutes for handoff.

## Exact change boundary and ownership

Recommended repository author: an explicitly assigned tuner, leaving Claude's
existing P claim alone. Reviewer: baton.codex. Deployment/config acceptance and
recovery: the owner's authorized operations context. Do not ask the current
Claude holder to take a second Work. Assign file ownership before any writes.

1. `baton:AGENTS.md`, the non-interactive managed-turn section: add a paragraph
   requiring each Work turn, after its successful standalone claim and before
   execution, to consume complete current `work-events` handoff comments and
   the discussion threads located by `detail`. Follow pagination; preserve the
   current instruction bodies rather than filtering them out. Require
   successful canonical pass/return and a confirming state read before final,
   even after durable progress. Existing identity, Git, budget, test-change,
   independent-review and no-escalation rules stay authoritative.
2. `baton:docs/AGENTS-MAILBOX-PROTO.md`, readiness discipline, currently lines203-204:
   replace "Never end a turn holding work you have claimed and neither progressed
   nor handed back" with "Never end a turn holding a Work claim, even after
   recording progress. Pass completed Work or return incomplete Work through
   its authorized route, then confirm canonically that the claim is released."
   Add the current-handoff/discussion read instruction with a link to AGENTS.md.
   This removes the progress-only ambiguity without changing protocol semantics.
3. Deployment file `/home/sl/baton-v11.14aecfb/baton.json`: only
   `/teams/baton/roles/impl/instructions` and the required `/generation` bump.
   Preserve the existing role text and append exactly
   `MANAGED-TURN-INSTRUCTION-v1.txt` (one separating space). Exact before/after
   JSON values and baseline config SHA256 are in
   `evidence/config-change-proposal.json`; observed generation8, proposed9.
   This is an operator-owned deployment locator, not a dossier binding.
   No other role, participant, route, capability, runtime deadline, executable,
   adapter, permission or background-task setting may change in this scope.

Evidence writes belong only under this dossier; the actual author appends
PROGRESS.md, reviewer adds a fresh timestamped review, operations appends a
recovery receipt. No existing test path changes are proposed. No bridge or
application source path is authorized. No new implementation test is necessary
for prose and a config string; use the exact-delta and actual-delivery checks
below. Optional stopReason work is deferred.

## Actual delivery mechanism

The installed0650c61 `acp_baton_bridge.mjs` loads accepted role instructions once
at startup. `baton_readiness.mjs` includes that accepted text in every action
prompt, and the configured impl participant reads only its own role. A canonical
`regen` operation accepts the edited next-generation config; then the supported
lifecycle replacement loads it. The retained next prompt must contain the exact
appended instruction, with the existing binary/config/participant/role contract.
A config diff, plain discussion post, seen cursor or successful restart alone
does not prove delivery. No full discussion body is injected by the bridge;
the delivered instruction requires the model to read the authoritative thread.

The supported lifecycle recipes are `just stop /home/sl/baton-v11.14aecfb`,
`just start /home/sl/baton-v11.14aecfb`, and `just status /home/sl/baton-v11.14aecfb`.
They operate on the complete configured service set, including this reviewer's
backend. The stop/start pair therefore belongs in the operator's external
terminal; never improvise a selected-PID restart or issue a self-terminating
stop from the managed reviewer. No launcher or infrastructure manifest edits
are part of the proposal. Source: justfile and prior W114716 operational finding.

## Ordered correction and recovery

1. Owner accepts this exact bounded scope and operational budget, assigns its
   author, and keeps W133117 unreleased. Prepare policy edits and the config
   candidate, record exact before/after bytes and obtain independent review.
   Refuse unplanned overlap or drift before touching the live configuration.
2. Prepare the operator's external lifecycle terminal and record an executable
   stop/start/status checklist before any stop. Re-read canonical dispatch,
   W133117, runtime and incidents. Confirm no P execution or delegated resource
   remains; a failed state alone is not permission to kill an unproved process.
   Preserve the20-entry manifest and all P evidence/progress. If P has advanced
   since this snapshot, refresh the manifest under its actual custody and
   preserve the new cumulative spending; never restore older candidate bytes.
3. Once correction and recovery are ready, authorized operator drains dispatch
   to prevent new claims. Existing live claim holders must finish/pass normally;
   this planning Work and any ops Work must also relinquish claims before the
   operator expects `paused`. Never release another active task for convenience.
4. Under that drained boundary, re-read the exact orphan identity. The observed
   recovery operands are `work=W133117 expect=baton.claude episode=133349`, claim133353.
   Only if those remain current and the domain is proved settled, the recovery
   owner uses canonical `release` with a reason binding this reviewed correction,
   the preservation manifest and cumulative budget. Any mismatch refuses and
   returns for renewed evidence, never a blind retry with new operands.
   Wait for canonical paused state before lifecycle work; no raw-store changes.
5. Apply only the reviewed config JSON delta and accept it with canonical
   `regen` under the operator's own configured identity/capability. A concurrent
   config/generation change requires a fresh reviewed proposal, not overwriting
   it or guessing the next generation. Every Baton operation remains one direct
   invocation with the deployment's explicit binary, config and participant.
6. Operator performs the supported full stop/start pair while dispatch remains
   paused, then checks service health, configured role/session provenance,
   unchanged foreground-task flag and deadline. Verify P files and evidence
   still match the preservation manifest. A failure holds dispatch and records
   the exact condition; do not repeatedly restart or erase incident history.
7. Only after these checks, owner resumes dispatch. Retain the first corrected
   prompt and subsequent public tool results. Require a successful P claim,
   current handoff read and T133117 discussion read including M133314, plus the
   bound P dossier. Before any new product verification the author carries
   forward and reconciles the complete P spending history. Do not rerun gates
   solely to prove this operational correction.
8. Observe that this turn either completes the remaining P scope and passes to
   independent review or returns incomplete P to baton.bug with exact remaining
   work/evidence/spending. Confirm the canonical claim release precedes its
   final response. Read-only evidence of both delivery and proper settlement is
   the behavioral acceptance. A new held-claim ending is failure, not permission
   for another automatic release/redelivery. Owner then decides incident closure.

The runtime may receive other ordinary actions first after resume; preserve
their actual identities. Do not mislabel a poke response as a P Work handoff.
If no P turn has occurred, behavioral acceptance remains pending.

## Verification allocation proposed for owner acceptance

New standalone W133361 operational allocation: **120 seconds total** measured
command wall time, split15s author static checks,15s independent review,90s
operations/lifecycle verification. No automatic borrowing or second attempt.
Record every invocation/elapsed result, including failures, in this dossier.
The operations share includes stop/start/status waits; if safe completion needs
more time, report the exact remaining work and seek an explicit owner amendment
before beginning that phase. Do not use a budget timer to interrupt a lifecycle
operation already needed to restore the service set safely; any overrun must
be recorded and no further verification run begun without disposition.

Author/reviewer checks: exact two-file prose diff; role append byte equality;
only the two approved JSON pointers change; baseline digests and syntax valid;
repository whitespace check. No suite, application probe or live model smoke
test is requested. Runtime checks reuse the existing carrier; do not modify
tests to manufacture proof of successful delivery.

The existing P implementation turn's ordinary verification remains charged to
its77s author allowance (latest reported spend2.54s, not independently audited),
with8s independent P review unchanged. A source/profile probe's earlier final
and progress reports differ, so retain the full history and have the author
reconcile it before new runs; do not infer a fresh74.46s credit from one line.
NEW260s campaign reserves, other slices, old residual budgets and W119405 are
unavailable to this operational work. Observation of an existing implementation
turn does not commission extra product tests or reset its limits.

## Prepared artifacts and remaining decision

The accepted investigation and selected direction are pinned in FINDING.md.
`MANAGED-TURN-INSTRUCTION-v1.txt` supplies exact role text;
`evidence/config-change-proposal.json` supplies exact config values and base;
`evidence/recovery-preservation-133448.json` binds P files and current spending
claim. All are prepared without changing product files, live policy/config,
runtime or custody. Remaining owner decision is this proposal's bounded paths,
allocation and operator scheduling. Implementation/recovery follows only then.
