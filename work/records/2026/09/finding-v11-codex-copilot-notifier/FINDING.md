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


## 2026-09-21 — owner selects existing interactive conversation

Owner explicitly selects notification delivery to current conversation 01a0c23a-8904-73d3-a571-a5b9ed965404. Observed: running dispatcher maps baton-prompt to a different fresh-start context. Current conversation environment and session storage identify .codex. This supersedes the prior requirement to attach the UI to the newly minted prompt for this recovery.

Operational limitation: notifier cannot rebind its target; dispatcher has no live rebind control, and lifecycle CLI exposes whole-stack start/stop only. Bounded stopgap: preserve app-server and other context mappings, stop/relaunch only the dispatcher under its lifecycle lock and process-identity checks, updating its tracked process entry and rendered baton-prompt mapping. Refuse if another target has active/queued work. Keep backups. This is an operator recovery, not a product fix for missing prompt reattachment; a subsequent full stack start still mints a new prompt and requires explicit reattachment. Start exactly one notifier using its existing cursor/lock. No Work claims or other agents' turns are taken.

Reattachment applied and verified: dispatcher pid2812419 reports baton.prompt role prompt, loaded and connected, thread01a0c23a-8904-73d3-a571-a5b9ed965404, active during this interactive turn, with no quarantine. All other target thread IDs preserved; lifecycle process entry updated with verified identity. Notifier launch through the requested command was refused by the execution approval system (approval request failed). No successful watcher-start or UI delivery claim; owner terminal launch remains required.


## 2026-09-21T04:52Z — interactive prompt approval quarantines advisory delivery

Confirmed: after reattachment, prompt requested approval to launch the notifier at 04:48:56Z in human-initiated turn01a0c24a-1c59-7490-a0c3-ff1e4a6f011d. Dispatcher explicitly logged that this turn matched no delivery it recorded, yet denied its approval, quarantined baton-prompt and interrupted the interactive turn. Subsequent interactive turns work, but notifier admission remains fenced. The earlier successful mapping report was not successful advisory-delivery evidence. Prompt caused the triggering request while setting up the notifier.

Dry-run at snapshot226968 includes work:2b077949-W202663; reviewer claimed at 04:44:57Z and returned to baton.decide at 04:50:37Z. Missing notification is the prompt quarantine, not Work filtering or reviewer pickup. Proposed correction: distinguish managed/advisory delivery approval handling from human-origin interactive turns on prompt targets; preserve managed approval fences and do not clear quarantine as a workaround. Existing context recovery remains subject to its documented fresh-context boundary. No fix or fence removal applied.

## 2026-09-21 — restore the owner-selected fresh prompt mapping

Owner supplied conversation `01a0c245-7084-7450-aa08-18c41190d3ee` and requested restoration of app-server notifications such as W202663. The pre-reattachment dispatcher backup confirms this is the prompt created by the latest full stack start. This selection supersedes the earlier recovery's selection of `01a0c23a-8904-73d3-a571-a5b9ed965404`; that earlier context remains quarantined.

Revalidated live: one notifier is running, dry-run includes W202663, and dispatcher status still names the old quarantined prompt with `deliverable: false`. All other dispatcher targets are idle with empty queues. Bounded operational recovery restores the original fresh prompt mapping under the infrastructure lock, checks tracked process identity, backs up rendered config/state, and restarts only the dispatcher. Preserve all other mappings, the existing notifier/cursor, and every quarantine marker. Refuse if other targets become busy or the selected context has a fence. This is a deployment stopgap for the already-recorded attachment/approval defects, not their product fix. UI delivery remains unproved until an advisory actually appears after the human turn ends.
