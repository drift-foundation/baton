# V11 Codex copilot attention notifier

## 2026-09-07 — approved direction and implementation boundary

Owner requested `tools/codex_copilot_notifier.py` now, while other agents
continue v12 work. It is explicitly Codex-specific: canonical Baton reads
observe an operator's attention queue, then the existing Codex bridge starts
an advisory turn on the configured human-attached prompt thread. No second
context or readiness consumer, claims, approvals, workflow mutations, Git
operations, or autonomous repository changes are authorized by a notification.

Confirmed locally: the bridge supports generic events and per-target busy
state, but its generic formatter suggests fixing changes. Dispatcher-owned
turns deny interactive approvals. This implementation adds an advisory-only
formatter and prompt-only idle admission; it does NOT relax approval handling.
If a read requires new permission, the copilot reports commands for the owner.

Scope: new watcher, focused tests and usage documentation; additive event
formatter/admission/status changes and tests in the existing v11 bridge.
No v12 paths, infra lifecycle/config changes, or live startup. The Work binding
is this record. Execution by baton.prompt under the owner's authorized claim.

Delivery is advisory, not a transaction: persist socket-accepted attention
versions, not a claim or proof of completed model analysis. A bridge restart
or changed prompt thread reconciles by offering current attention again;
duplicates across failures are safe. Failed model turns need manual retry.
While busy, no events are sent; the next poll rebuilds/coalesces current state.
Stale queued advice always requires canonical re-read. No exact-once promise.

First live rollout must verify the configured thread is the owner's attached
UI and that the summary appears there. Offline proof does not establish that.

## 2026-09-07 — owner accepts bounded rollout

After independent sign-off in review-2026-09-07T13-34-37Z.md, Slawomir accepted
the rollout and asked for operator commands. Preparation-only/no-live-enable
scope above is superseded solely for owner-run drain, restart and one-notifier
poll with visible UI confirmation, followed by the foreground watcher if that
proof succeeds. No autonomous approval, schema activation or Git change.

Deployment inspection confirms codex-dispatcher launches the source checkout's
bridge, so a new Baton/TUI distribution is unnecessary. Full infra start mints
new prompt contexts; the operator must attach to the newly configured
baton-prompt thread before the proof. The old conversation is not implicitly
reattached and no transcript/history continuity is claimed by this rollout.
Exact notifier configuration prepared at
/tmp/baton-copilot-notifier-preview.cxwtwI/rollout.json, for installation as
/home/sl/baton-v11.14aecfb/codex-copilot-notifier.json. It observes baton.slaw,
targets baton.prompt and stores its advisory cursor beneath the existing run/
directory. This approval is not evidence of a completed live notification.

## 2026-09-07 — independent candidate review

**Confirmed:** baton.codex signed off the bounded seven-path implementation
under claim 110517; no blocking defect found. Exact review: `review-2026-09-07T13-34-37Z.md`.
Candidate manifest: `evidence/review-110517/candidate-manifest.json`, SHA-256
`e957fa6849bdac2b671572301293c4dd29188d2c9bb9eb5cf09889962c21f457`.
The independent offline probe preserves all nine admission fences and existing
thread delivery/ordinary status behavior. Existing bridge tests changed only
by addition; prior assertions remain intact.

**Open:** owner-controlled deployment and proof that the advisory appears in
the attached UI. No live rollout, new context, provider turn or infrastructure
change occurred during independent review. The earlier delivery limitations
and approval-policy boundary remain in force.
